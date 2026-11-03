export type TokenHandoffAgente = {
  /** tipo do agente (subagentType), curto */
  tipo: string
  /** descricao curta, ja truncada e sem quebras de linha */
  descricao: string
  /** caminho de handoff extraido por regex estrita, se houver */
  handoff?: string
  /** tokens medidos pelos turnos do agente (entrada nova + saida + cache escrito) */
  porTurno: number
  /** totalTokens informado pelo resultado da ferramenta Agent, se houver */
  porFerramenta?: number
}

export type TokenHandoffSessao = {
  /** id da sessao a que o contador pertence; muda no /clear */
  sid: string
  /** tokens acumulados do contexto principal: soma dos incrementos positivos de context.tokens (nunca diminui) */
  acumPrincipal: number
  /** ultimo context.tokens lido (base do proximo incremento; cai na compactacao sem subtrair) */
  ultimoCtx: number
  /** agentes por id */
  agentes: Record<string, TokenHandoffAgente>
  /** marco (400000) ja disparado, sem repeticao */
  disparados: number[]
  /** 400k cruzado: bloqueio de agentes e protocolo obrigatorio */
  duro: boolean
  /** handoff automatico (sessao nova + encerramento) ja tentado nesta sessao */
  handoff?: boolean
}

declare module 'claude-code' {
  interface PluginState {
    'token-handoff': { sessao: TokenHandoffSessao }
  }
}
