export interface Query {
  id: number;
  nome: string;
  area: string;
  tabelas: string;
  qtdTabelas: number;
  replicadaHana: '' | 'sim' | 'nao' | 'parcial';
  complexidade: '' | 'baixa' | 'media' | 'alta';
  volumetria: string;
  esforcoHana: number;
  esforcoGcp: number;
  observacoes: string;
}

export interface Tabela {
  id: number;
  nome: string;
  usadaPor: string;
  replicadaHana: 'sim' | 'nao' | 'parcial';
  volumetria: string;
  frequencia: '' | 'realtime' | 'diaria' | 'semanal' | 'mensal';
  prioridade: 'baixa' | 'media' | 'alta';
}

export interface Custos {
  hanaProjeto: number;
  hanaRecorrente: number;
  gcpProjeto: number;
  gcpStorage: number;
  gcpCompute: number;
  incentivoPSF: number;
  incentivoGoogle: number;
}

export interface Metricas {
  totalQueries: number;
  queriesMapeadas: number;
  percMapeamento: string;
  replicadasSim: number;
  replicadasNao: number;
  replicadasParcial: number;
  percReplicadas: string;
  complexidadeAlta: number;
  totalEsforcoHana: string;
  totalEsforcoGcp: string;
  tabelasUnicas: number;
  tabelasReplicadasHana: number;
  tabelasPendentes: number;
  percTabelasReplicadas: string;
  custoTotalHana: string;
  custoTotalGcp: string;
  economiaGcp: string;
}