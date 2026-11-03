import type { EngineInterface, Register } from 'claude-code'
import type { TokenHandoffSessao as Sessao } from '../types/index.d.ts'

const REF = { plugin: 'token-handoff', key: 'sessao' } as const
const DURO = 400_000
const MARCOS = [DURO] as const
const DESC_MAX = 120
const HANDOFF = /docs\/operations\/handoffs\/[A-Za-z0-9_.-]{1,60}\.md/
const HANDOFF_G = new RegExp(HANDOFF.source, 'g')
const SAIDA = /(grav|escrev|salv|write|sa[ií]da|output|devolv|entregu)[^\n]{0,60}$/i
const LINHA_MAX = 400
// traits de requisicoes que NAO sao a conversa principal: sem injecao (SEC-MOD-03). lean/bare NAO suprimem (SEC-MOD-10)
const TRAITS_NAO_PRINCIPAL = ['teammate', 'analysis'] as const
const NEGA =
  'Marco de 400k tokens atingido: novos despachos de agentes estão bloqueados. Registre a memória do projeto, grave o prompt de continuação e encerre a sessão.'

const SECAO_DURO =
  'MARCO OBRIGATÓRIO DE 400K TOKENS (mod token-handoff; somente para a sessão principal, subagentes e teammates ignoram): NÃO pergunte ao usuário e NÃO despache agente novo (o mod nega). ' +
  'Faça, nesta ordem: (1) deixe terminar os agentes em andamento e registre seus resultados; (2) registre na memória do projeto tudo que a ' +
  'próxima sessão precisa (estado, hashes, decisões, pendências); (3) grave docs/operations/prompt-continuacao-sessao-<AAAA-MM-DD>.md ' +
  '(o que ler primeiro, estado, próximo passo, o que NÃO fazer); (4) termine o turno com uma linha avisando o caminho do prompt. Assim que o arquivo existir ' +
  'e não houver agente ativo, o mod abre a nova sessão com esse prompt e encerra esta automaticamente: não rode comandos para isso.'

const vazio = (sid: string): Sessao => ({
  sid,
  acumPrincipal: 0,
  ultimoCtx: 0,
  agentes: {},
  disparados: [],
  duro: false,
})

const SEGREDO = [
  /\b(?:authorization\b\s*[:=]?\s*)?(?:bearer|basic)\s+\S+/gi,
  /\b(?:password|passwd|senha|secret|segredo|token|api[_-]?key|apikey|authorization|bearer)\b\s*[:=]?\s*\S+/gi,
  /\b(?:AKIA|ASIA)[0-9A-Z]{16}\b/g,
  /\b(?:sk|pk|ghp|gho|ghs|xox[abpr]|glpat|npm)[-_][A-Za-z0-9_-]{8,}/g,
  /\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_.-]+/g,
  /[A-Za-z0-9_\-+/=]{20,}/g,
]

// Texto livre (vem do modelo): sem controles/quebras Unicode, sem segredos, sem markdown, limitado.
const curto = (s: string, n = DESC_MAX): string => {
  let limpo = s
    .replace(/[\u0000-\u001f\u007f-\u009f\u2028\u2029]/g, ' ')
    .replace(/[\u200b-\u200f\u202a-\u202e\u2060-\u2069\ufeff]/g, '')
  for (const r of SEGREDO) limpo = limpo.replace(r, '[omitido]')
  limpo = limpo.replace(/[`*_\[\]<>#|~"\\]/g, '').replace(/\s+/g, ' ').trim()
  // QA-MOD-01: redige de novo apos remover markdown (os caracteres removidos podem reconstituir um padrao)
  for (const r of SEGREDO) limpo = limpo.replace(r, '[omitido]')
  return limpo.length > n ? `${limpo.slice(0, n - 1)}…` : limpo
}

const ident = (s: string): string => s.replace(/[^A-Za-z0-9_-]/g, '').slice(0, 40)

// Caminho de handoff: normaliza "\"; prefere a descricao; no prompt so o trecho precedido de verbo de saida.
const acharHandoff = (descricao: string, prompt: string): string | undefined => {
  const d = descricao.replace(/\\/g, '/')
  const dd = d.match(HANDOFF)
  if (dd) return dd[0]
  const p = prompt.replace(/\\/g, '/')
  for (const m of p.matchAll(HANDOFF_G)) {
    if (SAIDA.test(p.slice(Math.max(0, (m.index ?? 0) - 80), m.index ?? 0))) return m[0]
  }
  return undefined
}

const num = (x: unknown): number => (typeof x === 'number' && Number.isFinite(x) && x > 0 ? x : 0)
const pad = (n: number): string => String(n).padStart(2, '0')
const rotulo = (m: number): string => `${m / 1000}k`

const somaAgentes = (s: Sessao): number =>
  Object.values(s.agentes).reduce((t, a) => t + (a.porFerramenta ?? a.porTurno), 0)
// QA-MOD-03: total ACUMULADO e monotono = soma dos incrementos positivos de context.tokens + tokens de subagentes
const total = (s: Sessao): number => s.acumPrincipal + somaAgentes(s)

// QA-MOD-02: bloqueio de 400k tambem em memoria do modulo (sobrevive a falha de state.set); chave = id da sessao
let duroMem: string | undefined
const duroDe = (s: Sessao): boolean => s.duro || duroMem === s.sid

// Fila em memoria: o diario so acrescenta; ler e gravar ocorrem em serie.
let fila: Promise<void> = Promise.resolve()

async function ler($: EngineInterface): Promise<{ s: Sessao; v: number }> {
  const sid = await $.session.id()
  const { value, version } = await $.state.get(REF)
  if (value === undefined || value.sid !== sid) return { s: vazio(sid), v: version }
  return { s: value, v: version }
}

// Atualiza o estado com repeticao em caso de corrida (ifVersion).
async function mudar($: EngineInterface, f: (s: Sessao) => void): Promise<Sessao> {
  for (let i = 0; i < 5; i++) {
    const { s, v } = await ler($)
    f(s)
    const r = await $.state.set(REF, s, { ifVersion: v })
    if (r.isSet) return s
  }
  const { s } = await ler($)
  return s
}

// Unica escrita em disco do mod: acrescenta uma linha ao diario do dia.
async function diario($: EngineInterface, linha: string): Promise<void> {
  fila = fila.then(async () => {
    try {
      const cwd = (await $.session.cwd()).replace(/\\/g, '/').replace(/\/$/, '')
      const d = new Date(await $.clock.now())
      const dia = `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
      const hora = `${pad(d.getHours())}:${pad(d.getMinutes())}`
      // so em projeto com .engineering/project.json (SEC-MOD-07)
      if (!(await $.fs.exists(`${cwd}/.engineering/project.json`))) return
      // arquivo SEPARADO e de escritor unico (este mod); o .md da sessao principal nunca e tocado
      const arq = `${cwd}/docs/operations/diario-sessao-${dia}.mod.md`
      const antes = (await $.fs.exists(arq)) ? await $.fs.read(arq) : ''
      const sep = antes === '' || antes.endsWith('\n') ? '' : '\n'
      const texto = `- ${hora} [mod] ${linha}`.replace(/[\u0000-\u001f\u007f-\u009f\u2028\u2029]/g, ' ').slice(0, LINHA_MAX)
      await $.fs.write(arq, `${antes}${sep}${texto}\n`)
    } catch (erro) {
      // o diario e melhor esforco; nunca quebra a sessao
      $.ui.log(`token-handoff: diario nao gravado (${String(erro).slice(0, 80)})`, { to: 'debug' })
    }
  })
  await fila
}

// Le o contexto principal, atualiza o pico e registra os marcos recem cruzados.
async function atualizar($: EngineInterface): Promise<Sessao> {
  const uso = await $.session.usage()
  const tokens = num(uso.context.tokens)
  let novos: number[] = []
  const s = await mudar($, (x) => {
    if (tokens > x.ultimoCtx) x.acumPrincipal += tokens - x.ultimoCtx
    x.ultimoCtx = tokens
    const t = total(x)
    novos = MARCOS.filter((m) => t >= m && !x.disparados.includes(m))
    if (novos.length > 0) {
      x.disparados.push(...novos)
      x.duro = true
    }
    if (x.duro) duroMem = x.sid
  })
  for (const m of novos) {
    await diario($, `marco ${rotulo(m)} tokens cruzado (total estimado ${total(s)} tokens)`)
    $.ui.toast(
      `Marco ${rotulo(m)} tokens: novos agentes bloqueados; registrando memória e passando para a sessão nova.`,
    )
  }
  return s
}

// Falha fechada (SEC-MOD-02): erro ao atualizar consulta `duro`; indeterminavel nega.
async function bloqueado($: EngineInterface): Promise<boolean> {
  try {
    return duroDe(await atualizar($))
  } catch {
    try {
      return duroDe((await ler($)).s)
    } catch {
      return true
    }
  }
}

// Handoff automatico (400k): com o prompt de continuacao gravado e nenhum agente ativo, abre a sessao nova e encerra esta.
// Uma unica tentativa por sessao (x.handoff); falha so vai ao diario e ao log, nunca quebra o turno.
async function handoff($: EngineInterface): Promise<void> {
  const { s } = await ler($)
  if (!duroDe(s) || s.handoff) return
  try {
    const ativos = (await $.agent.list()).filter((a) => a.status === 'running' || a.status === 'pending' || a.status === 'waiting')
    if (ativos.length > 0) return
    const cwd = (await $.session.cwd()).replace(/\\/g, '/').replace(/\/$/, '')
    const d = new Date(await $.clock.now())
    const dia = `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
    const prompt = `${cwd}/docs/operations/prompt-continuacao-sessao-${dia}.md`
    if (!(await $.fs.exists(prompt))) return
    await mudar($, (x) => {
      x.handoff = true
    })
    // o instalador grava o script no escopo escolhido: projeto (.claude/scripts) tem precedencia sobre o global (~/.claude/scripts)
    const local = `${cwd}/.claude/scripts/handoff-sessao.ps1`
    const global = `${((await $.env.get('USERPROFILE')) ?? '').replaceAll(String.fromCharCode(92), '/')}/.claude/scripts/handoff-sessao.ps1`
    const script = (await $.fs.exists(local)) ? local : global
    await diario($, `handoff automatico: abrindo sessao nova com ${prompt.slice(cwd.length + 1)} e encerrando esta`)
    const r = await $.process.run(
      ['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', script, '-PromptFile', prompt, '-Cwd', cwd],
      { timeoutMs: 20_000 },
    )
    if (r.exitCode !== 0) {
      await diario($, `handoff falhou (exit ${r.exitCode}): ${curto(r.stderr, 100)}`)
      $.ui.toast('Handoff automático falhou; abra a nova sessão manualmente.')
    }
  } catch (erro) {
    $.ui.log(`token-handoff: handoff falhou (${String(erro).slice(0, 80)})`, { to: 'debug' })
  }
}

export const register: Register = (on) => {
  on('turn.start', async ($, e, next) => {
    if (e.agentId === undefined) await atualizar($).catch(() => undefined)
    return next(e)
  })

  on('turn.complete', async ($, e, next) => {
    try {
      if (e.agentId !== undefined) {
        const id = e.agentId
        const u = e.usage
        const novo = u ? num(u.input_tokens) + num(u.output_tokens) + num(u.cache_creation_input_tokens) : 0
        const s = await mudar($, (x) => {
          const a = x.agentes[id] ?? { tipo: 'desconhecido', descricao: '', porTurno: 0 }
          a.porTurno += novo
          x.agentes[id] = a
        })
        const a = s.agentes[id]
        const h = a?.handoff ? ` handoff=${a.handoff}` : ''
        await diario($, `fim de agente: tipo=\`${a?.tipo ?? 'desconhecido'}\` status=\`${curto(String(e.reason), 20)}\` id=${ident(id)}${h}`)
        await atualizar($)
      } else {
        await atualizar($)
        await handoff($)
      }
    } catch {
      // nunca quebra o fim do turno
    }
    return next(e)
  })

  on('agent.spawn', async ($, e, next) => {
    if (await bloqueado($)) return { deny: NEGA }
    const r = await next(e)
    const id = 'agentId' in r ? r.agentId : undefined
    if (typeof id === 'string') {
      const tipo = curto(e.subagentType, 40)
      const descricao = curto(e.description)
      // so o caminho, por regex estrita; o texto do prompt nunca e guardado
      const handoff = acharHandoff(e.description, e.prompt)
      await mudar($, (x) => {
        x.agentes[id] = { tipo, descricao, handoff, porTurno: x.agentes[id]?.porTurno ?? 0 }
      }).catch(() => undefined)
      await diario(
        $,
        `despacho de agente: tipo=\`${tipo}\` desc=\`${descricao}\` id=${ident(id)}${handoff ? ` handoff=${handoff}` : ''}`,
      )
    }
    return r
  }).catch(async ($, e, next) => {
    // falha do guarda: fecha se 400k cruzado ou se o estado for indeterminavel
    const duro = await ler($).then((x) => duroDe(x.s), () => true)
    return duro ? { deny: NEGA } : next(e)
  })

  on('tool.call', { tool: 'Agent' }, async ($, e, next) => {
    if (await bloqueado($)) return { deny: NEGA }
    const r = await next(e)
    try {
      const rec = r.deny === undefined ? (r.result as { agentId?: unknown; totalTokens?: unknown } | undefined) : undefined
      const t = num(rec?.totalTokens)
      if (typeof rec?.agentId === 'string' && t > 0) {
        const id = rec.agentId
        await mudar($, (x) => {
          const a = x.agentes[id] ?? { tipo: 'desconhecido', descricao: '', porTurno: 0 }
          a.porFerramenta = t
          x.agentes[id] = a
        })
        await atualizar($)
      }
    } catch {
      // a medicao e melhor esforco
    }
    return r
  }).catch(async ($, e, next) => {
    const duro = await ler($).then((x) => duroDe(x.s), () => true)
    return duro ? { deny: NEGA } : next(e)
  })

  // Custo zero de tokens: so injeta quando um marco exige (encerrando ou duro).
  on('prompt.compose', async ($, e, next) => {
    const r = await next(e)
    try {
      const { s } = await ler($)
      if (!duroDe(s)) return r
      if (e.traits.some((x) => (TRAITS_NAO_PRINCIPAL as readonly string[]).includes(x))) return r
      const id = 'token-handoff:marco'
      return { sections: [...r.sections, { id, text: SECAO_DURO, scope: 'session' as const }] }
    } catch {
      return r
    }
  })
}
