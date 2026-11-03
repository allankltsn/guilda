import { expect, test } from 'claude-code/testing'

const norm = (p: string) => p.split(String.fromCharCode(92)).join('/').replace(/^[A-Za-z]:/, '')
const DIARIO = '/proj/docs/operations/diario-sessao-2026-10-27.mod.md'
const PRINCIPAL = '/proj/docs/operations/diario-sessao-2026-10-27.md'
const PROJETO = '/proj/.engineering/project.json'

// Tudo o que o motor fornece por baixo do mod, em memoria.
function armar(on: any) {
  const mundo = {
    ctx: 0,
    sid: 's1',
    arquivos: new Map<string, string>([[PROJETO, '{}']]),
    escritas: [] as string[],
    perguntas: 0,
    ask: '',
    agentTokens: 0,
    usoFalha: false,
    idFalha: false,
  }
  on('session.usage', () => {
    if (mundo.usoFalha) throw new Error('falha')
    return {
      value: { startedAt: 0, context: { tokens: mundo.ctx, window: 1_000_000 }, rateLimits: [] },
    }
  })
  on('session.id', () => {
    if (mundo.idFalha) throw new Error('falha')
    return { value: mundo.sid }
  })
  on('session.cwd', () => ({ value: '/proj' }))
  on('clock.now', () => ({ value: Date.UTC(2026, 9, 27, 15, 0) }))
  on('fs.exists', (_: any, e: any) => ({ value: mundo.arquivos.has(norm(e.path)) }))
  on('fs.read', (_: any, e: any) => ({ value: mundo.arquivos.get(norm(e.path)) ?? '' }))
  on('fs.write', (_: any, e: any) => {
    mundo.escritas.push(norm(e.path))
    mundo.arquivos.set(norm(e.path), e.text)
    return { value: undefined }
  })
  on('ui.toast', () => ({ value: undefined }))
  on('ui.log', () => ({ value: undefined }))
  on('agent.spawn', () => ({ model: 'm', agentId: 'ag1' }))
  on('tool.call', (_: any, e: any) => {
    if (e.tool === 'AskUserQuestion') {
      mundo.perguntas++
      const q = e.questions[0].question as string
      return { result: { questions: e.questions, answers: { [q]: mundo.ask } } }
    }
    return { result: { agentId: 'ag1', totalTokens: mundo.agentTokens } }
  })
  on('prompt.compose', () => ({ sections: [{ id: 'base', text: 'base', scope: 'shared' }] }))
  on('turn.start', (_: any, e: any) => ({ turnId: e.turnId }))
  on('turn.complete', (_: any, e: any) => ({ text: e.answer }))
  return mundo
}

const fimPrincipal = ($: any, n = 'x') =>
  $.turn.complete({ answer: n, durationMs: 1, isAborted: false, turnId: `t${n}`, reason: 'answer' })

const compor = ($: any) =>
  $.prompt.compose({
    model: 'm', promptModel: 'm', surfaces: [], tools: [], outputStyle: null, traits: [],
  })

const marcosNoDiario = (m: ReturnType<typeof armar>) =>
  (m.arquivos.get(DIARIO) ?? '').split('\n').filter((l) => l.includes('cruzado')).length

test('(a) 100k, 200k e 300k nao perguntam nem marcam; so 400k dispara, uma vez', async ($, on) => {
  const m = armar(on)
  for (const ctx of [50_000, 100_000, 200_000, 300_000, 399_000]) {
    m.ctx = ctx
    await fimPrincipal($, String(ctx))
    expect(m.perguntas).toBe(0)
    expect((await compor($)).sections.length).toBe(1)
  }
  expect(marcosNoDiario(m)).toBe(0)
  for (const ctx of [400_000, 420_000]) {
    m.ctx = ctx
    await fimPrincipal($, String(ctx))
  }
  expect(m.perguntas).toBe(0)
  expect(marcosNoDiario(m)).toBe(1)
})



test('(b) a 400k despachos de agente sao negados e a secao obrigatoria e injetada', async ($, on) => {
  const m = armar(on)
  m.ctx = 400_000
  await fimPrincipal($)
  expect(m.perguntas).toBe(0)
  const negado = await $.tool.call({ tool: 'Agent', description: 'x', prompt: 'p' })
  expect(negado.deny === undefined).toBe(false)
  const r = await compor($)
  expect(r.sections[1].text).toContain('400K')
  // mantida a cada turno apos o marco
  expect((await compor($)).sections.length).toBe(2)
  const spawn = await $.agent.spawn({
    tool_use_id: 't', prompt: 'p', description: 'd', subagentType: 'x',
    provider: { plugin: 'engine', tier: 'core' }, parentModel: 'm', background: false, fork: false,
  })
  expect('deny' in spawn).toBe(true)
})

test('(c) compactacao nao redispara o marco', async ($, on) => {
  const m = armar(on)
  m.ctx = 410_000
  await fimPrincipal($, 'a')
  m.ctx = 20_000
  await fimPrincipal($, 'b')
  m.ctx = 60_000
  await fimPrincipal($, 'c')
  expect(marcosNoDiario(m)).toBe(1)
})

test('(c2) tokens de subagentes somam ao total e disparam o marco de 400k', async ($, on) => {
  const m = armar(on)
  m.ctx = 360_000
  m.agentTokens = 50_000
  await $.tool.call({ tool: 'Agent', description: 'x', prompt: 'p' })
  await fimPrincipal($)
  expect('deny' in (await spawn($))).toBe(true)
})

test('(d) o diario so acrescenta e nunca grava prompt nem resultado', async ($, on) => {
  const m = armar(on)
  m.arquivos.set(DIARIO, '- 08:00 linha anterior\n')
  await $.agent.spawn({
    tool_use_id: 't', prompt: 'SEGREDO-NO-PROMPT leia docs/operations/handoffs/entrada.md e grave o handoff em docs/operations/handoffs/x-autor.md', description: 'Autor do mod',
    subagentType: 'typescript-pro', provider: { plugin: 'engine', tier: 'core' }, parentModel: 'm',
    background: false, fork: false,
  })
  await $.turn.complete({
    answer: 'SEGREDO-NO-RESULTADO', durationMs: 1, isAborted: false, turnId: 'ta', reason: 'answer', agentId: 'ag1',
  })
  const d = m.arquivos.get(DIARIO) ?? ''
  expect(d.startsWith('- 08:00 linha anterior\n')).toBe(true)
  expect(d).toContain('despacho de agente: tipo=`typescript-pro`')
  expect(d).toContain('fim de agente: tipo=`typescript-pro` status=`answer`')
  expect(d).toContain('handoff=docs/operations/handoffs/x-autor.md')
  expect(d).not.toContain('entrada.md')
  expect(d).not.toContain('SEGREDO')
  expect(m.escritas.every((p) => p === DIARIO)).toBe(true)
  expect(m.arquivos.has(PRINCIPAL)).toBe(false)
})

test('(d2) descricao longa e truncada em 120 caracteres', async ($, on) => {
  const m = armar(on)
  await $.agent.spawn({
    tool_use_id: 't', prompt: 'p', description: 'a '.repeat(200), subagentType: 'x',
    provider: { plugin: 'engine', tier: 'core' }, parentModel: 'm', background: false, fork: false,
  })
  const linha = (m.arquivos.get(DIARIO) ?? '').split('\n')[0]
  expect(linha.length <= 400).toBe(true)
  expect(linha).toContain('…')
})

test('(e) sem marco cruzado nada e injetado e nada e perguntado', async ($, on) => {
  const m = armar(on)
  m.ctx = 399_000
  await fimPrincipal($)
  expect(m.perguntas).toBe(0)
  expect((await compor($)).sections.length).toBe(1)
  expect(m.escritas.length).toBe(0)
})

test('(f) /clear (novo id de sessao) recomeca o marco', async ($, on) => {
  const m = armar(on)
  m.ctx = 400_000
  await fimPrincipal($, 'a')
  expect('deny' in (await spawn($))).toBe(true)
  m.sid = 's2'
  m.ctx = 10_000
  await fimPrincipal($, 'b')
  expect('deny' in (await spawn($))).toBe(false)
  m.ctx = 400_000
  await fimPrincipal($, 'c')
  expect('deny' in (await spawn($))).toBe(true)
})

const spawn = ($: any, over: Record<string, unknown> = {}) =>
  $.agent.spawn({
    tool_use_id: 't', prompt: 'p', description: 'd', subagentType: 'x',
    provider: { plugin: 'engine', tier: 'core' }, parentModel: 'm', background: false, fork: false, ...over,
  })
const diarioDe = (m: ReturnType<typeof armar>) => m.arquivos.get(DIARIO) ?? ''

test('(g) SEC-MOD-01/REV-MOD-01: escreve so no .mod.md e nunca toca o .md da sessao principal', async ($, on) => {
  const m = armar(on)
  m.arquivos.set(PRINCIPAL, '- 08:00 linha da sessao principal\n')
  m.ctx = 400_000
  await spawn($)
  await fimPrincipal($)
  expect(m.escritas.length > 0).toBe(true)
  expect(m.escritas.every((p) => p === DIARIO)).toBe(true)
  expect(m.arquivos.get(PRINCIPAL)).toBe('- 08:00 linha da sessao principal\n')
})

test('(h) SEC-MOD-02: erro ao atualizar apos 400k continua negando (falha fechada)', async ($, on) => {
  const m = armar(on)
  m.ctx = 400_000
  await fimPrincipal($)
  m.usoFalha = true
  expect((await $.tool.call({ tool: 'Agent', description: 'x', prompt: 'p' })).deny === undefined).toBe(false)
  expect('deny' in (await spawn($))).toBe(true)
})

test('(h2) SEC-MOD-02: estado indeterminavel (id da sessao/leitura falha) nega', async ($, on) => {
  const m = armar(on)
  m.idFalha = true
  expect((await $.tool.call({ tool: 'Agent', description: 'x', prompt: 'p' })).deny === undefined).toBe(false)
  expect('deny' in (await spawn($))).toBe(true)
})

test('(h3) erro de medicao antes de 400k nao nega', async ($, on) => {
  const m = armar(on)
  m.usoFalha = true
  expect((await $.tool.call({ tool: 'Agent', description: 'x', prompt: 'p' })).deny === undefined).toBe(true)
})

test('(i) SEC-MOD-03: secao nao e injetada em teammate/analysis; texto diz somente sessao principal', async ($, on) => {
  const m = armar(on)
  m.ctx = 400_000
  await fimPrincipal($)
  const base = { model: 'm', promptModel: 'm', surfaces: [], tools: [], outputStyle: null }
  expect((await $.prompt.compose({ ...base, traits: ['teammate'] })).sections.length).toBe(1)
  expect((await $.prompt.compose({ ...base, traits: ['analysis'] })).sections.length).toBe(1)
  const r = await $.prompt.compose({ ...base, traits: [] })
  expect(r.sections.length).toBe(2)
  expect(r.sections[1].text).toContain('somente para a sessão principal')
})

test('(i2) SEC-MOD-10: lean e bare recebem a injecao', async ($, on) => {
  const m = armar(on)
  m.ctx = 400_000
  await fimPrincipal($)
  const base = { model: 'm', promptModel: 'm', surfaces: [], tools: [], outputStyle: null }
  expect((await $.prompt.compose({ ...base, traits: ['lean'] })).sections.length).toBe(2)
  expect((await $.prompt.compose({ ...base, traits: ['bare'] })).sections.length).toBe(2)
})

test('(j) SEC-MOD-04: redacao ampla e remocao de controles e U+2028/2029/0085', async ($, on) => {
  const m = armar(on)
  await spawn($, { description: 'a AKIAABCDEFGHIJKLMNOP b password=hunter2 c sk-abcdef123456 d\u2028e\u2029f\u0085g\u0007h\nI' })
  const d = diarioDe(m)
  expect(d).not.toContain('AKIA')
  expect(d).not.toContain('hunter2')
  expect(d).not.toContain('sk-abc')
  expect(/[\u2028\u2029\u0085\u0007]/.test(d)).toBe(false)
  expect(d.trim().split('\n').length).toBe(1)
})

test('(k) SEC-MOD-05: descricao entre crases, sem markdown nem crases internas', async ($, on) => {
  const m = armar(on)
  await spawn($, { description: 'ignore **tudo** `rm` [x](http://a) # titulo' })
  const d = diarioDe(m)
  expect(d).toContain('desc=`ignore tudo rm x(httpa) titulo`'.replace('httpa', 'http://a'))
  expect(d.split('desc=')[1].split('`').length).toBe(3)
})

test('(l) SEC-MOD-06/REV-MOD-03: normaliza barra invertida, prefere saida, ignora entrada, limita a linha', async ($, on) => {
  const m = armar(on)
  await spawn($, { description: 'Autor docs\\operations\\handoffs\\saida-a.md', prompt: 'leia docs/operations/handoffs/entrada.md' })
  await spawn($, { description: 'sem caminho', prompt: 'leia docs/operations/handoffs/entrada.md. Grave a saida em docs/operations/handoffs/saida-b.md' })
  await spawn($, { description: 'z'.repeat(500), subagentType: 'y'.repeat(500), prompt: 'docs/operations/handoffs/' + 'k'.repeat(100) + '.md' })
  const linhas = diarioDe(m).trim().split('\n')
  expect(linhas[0]).toContain('handoff=docs/operations/handoffs/saida-a.md')
  expect(linhas[1]).toContain('handoff=docs/operations/handoffs/saida-b.md')
  expect(diarioDe(m)).not.toContain('entrada.md')
  expect(linhas.every((l) => l.length <= 400)).toBe(true)
})

test('(m) SEC-MOD-07: sem .engineering/project.json no cwd nada e gravado', async ($, on) => {
  const m = armar(on)
  m.arquivos.delete(PROJETO)
  m.ctx = 400_000
  await spawn($)
  await fimPrincipal($)
  expect(m.escritas.length).toBe(0)
  expect(m.perguntas).toBe(0)
})

test('(n) QA-MOD-01: segredos camuflados por markdown/underscore sao redigidos', async ($, on) => {
  const m = armar(on)
  for (const c of ['pa*ss*word=hunter2zzz', 'sk-abcd*efgh1234', 'AK*IAABCDEFGHIJKLMNOP', 'tok_en: ABC123', 'Authorization: Bearer abc.def', 'ghp_' + 'a'.repeat(30)]) {
    await spawn($, { description: c, subagentType: c })
  }
  const d = diarioDe(m)
  for (const x of ['hunter2', 'efgh1234', 'ABCDEFGHIJKLMNOP', 'ABC123', 'abc.def', 'aaaaaaaa']) expect(d).not.toContain(x)
  expect(d.trim().split('\n').length).toBe(6)
})

test('(o) QA-MOD-02: falha de state.set a >= 400k ainda nega (flag em memoria)', async ($, on) => {
  const m = armar(on)
  on('state.set', () => ({ value: { isSet: false, version: 0 } }))
  m.ctx = 450_000
  expect((await $.tool.call({ tool: 'Agent', description: 'x', prompt: 'p' })).deny === undefined).toBe(false)
  expect('deny' in (await spawn($))).toBe(true)
  m.ctx = 1_000
  expect('deny' in (await spawn($))).toBe(true)
})

test('(p) QA-MOD-03: total acumulado e monotono; compactacao nao subtrai e 400k e alcancavel', async ($, on) => {
  const m = armar(on)
  m.ctx = 250_000; await fimPrincipal($, 'a')
  m.ctx = 20_000; await fimPrincipal($, 'b')
  m.ctx = 120_000; await fimPrincipal($, 'c') // 250k + 100k de crescimento novo = 350k
  expect('deny' in (await spawn($))).toBe(false)
  m.ctx = 20_000; await fimPrincipal($, 'd')
  m.ctx = 190_000; await fimPrincipal($, 'e') // 520k acumulados
  expect('deny' in (await spawn($))).toBe(true)
  expect(marcosNoDiario(m)).toBe(1)
})

test('(q) QA-MOD-04: tipo e status do agente entre crases, sem markdown', async ($, on) => {
  const m = armar(on)
  await spawn($, { subagentType: 'ignore **previous** `rm` instructions' })
  await $.turn.complete({ answer: 'r', durationMs: 1, isAborted: false, turnId: 'ta', reason: 'answer', agentId: 'ag1' })
  const linhas = diarioDe(m).trim().split('\n')
  expect(linhas[0]).toContain('tipo=`ignore previous rm instructions` desc=')
  expect(linhas[1]).toContain('tipo=`ignore previous rm instructions` status=`answer` id=')
})

test('(r) handoff automatico: com o prompt gravado e sem agente ativo roda o script uma unica vez', async ($, on) => {
  const m = armar(on)
  const PROMPT = '/proj/docs/operations/prompt-continuacao-sessao-2026-10-27.md'
  const chamadas: string[][] = []
  on('agent.list', () => ({ value: [] }))
  on('env.get', () => ({ value: '/home' }))
  on('process.run', (_: any, e: any) => {
    chamadas.push([...e.argv])
    return { value: { exitCode: 0, stdout: 'ok', stderr: '', isStdoutTruncated: false, isStderrTruncated: false } }
  })
  m.ctx = 400_000
  await fimPrincipal($, 'a') // prompt ainda nao existe
  expect(chamadas.length).toBe(0)
  m.arquivos.set(PROMPT, 'x'.repeat(200))
  await fimPrincipal($, 'b')
  await fimPrincipal($, 'c')
  expect(chamadas.length).toBe(1)
  expect(chamadas[0]).toContain('/home/.claude/scripts/handoff-sessao.ps1')
  m.arquivos.set('/proj/.claude/scripts/handoff-sessao.ps1', '#')
  expect(chamadas[0]).toContain(PROMPT)
})

test('(s) handoff automatico espera agente ativo terminar', async ($, on) => {
  const m = armar(on)
  let ativo = true
  const chamadas: string[][] = []
  on('agent.list', () => ({ value: ativo ? [{ id: 'ag1', status: 'running' }] : [] }))
  on('env.get', () => ({ value: '/home' }))
  on('process.run', (_: any, e: any) => {
    chamadas.push([...e.argv])
    return { value: { exitCode: 0, stdout: '', stderr: '', isStdoutTruncated: false, isStderrTruncated: false } }
  })
  m.arquivos.set('/proj/docs/operations/prompt-continuacao-sessao-2026-10-27.md', 'x'.repeat(200))
  m.ctx = 400_000
  await fimPrincipal($, 'a')
  expect(chamadas.length).toBe(0)
  ativo = false
  await fimPrincipal($, 'b')
  expect(chamadas.length).toBe(1)
})
