import React, { useState, useMemo } from 'react';
import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Download, Plus, Trash2, CheckCircle, AlertCircle, TrendingUp } from 'lucide-react';

const QUERIES_INICIAIS = [
  { id: 1, nome: 'RSDRI-OTHERS', area: 'Outros' },
  { id: 2, nome: 'P_MED_MED01M_Q001', area: 'Medicamentos' },
  { id: 3, nome: 'PN_SRM_FORN_CONVIDADOS2', area: 'Fornecedores' },
  { id: 4, nome: 'PN_SRM_ITENS_OPP', area: 'Itens/Oportunidades' },
  { id: 5, nome: 'PN_SRM_JUSTIFICATIVA_DECLINIO', area: 'Fornecedores' },
  { id: 6, nome: 'P_SRM_SRM01_Q001', area: 'SRM01' },
  { id: 7, nome: 'P_SRM_SRM01_Q002', area: 'SRM01' },
  { id: 8, nome: 'P_SRM_SRM01_Q003', area: 'SRM01' },
  { id: 9, nome: 'P_SRM_SRM01_Q004', area: 'SRM01' },
  { id: 10, nome: 'P_SRM_SRM01_Q005', area: 'SRM01' },
  { id: 11, nome: 'P_SRM_SRM01_Q006', area: 'SRM01' },
  { id: 12, nome: 'P_SRM_SRM01_Q007', area: 'SRM01' },
  { id: 13, nome: 'P_SRM_SRM02_Q001', area: 'SRM02' },
  { id: 14, nome: 'P_SRM_SRM03_Q003', area: 'SRM03' },
  { id: 15, nome: 'P_SRM_SRM03_Q005', area: 'SRM03' },
  { id: 16, nome: 'P_SRM_SRM03_Q006', area: 'SRM03' },
  { id: 17, nome: 'P_SRM_SRM03_Q007', area: 'SRM03' },
  { id: 18, nome: 'P_SRM_SRM03_Q008', area: 'SRM03' },
  { id: 19, nome: 'P_SRM_SRM03_Q009', area: 'SRM03' },
  { id: 20, nome: 'P_SRM_SRM03_Q015', area: 'SRM03' },
  { id: 21, nome: 'P_SRM_SRM03_Q016', area: 'SRM03' },
  { id: 22, nome: 'P_SRM_SRM03_Q017', area: 'SRM03' },
  { id: 23, nome: 'P_SRM_SRM03_Q018', area: 'SRM03' },
  { id: 24, nome: 'P_DURACAO', area: 'Métricas' },
  { id: 25, nome: 'P_DTCRIA', area: 'Métricas' },
  { id: 26, nome: '0BBP_BIDDER', area: 'Licitação' }
];

export default function MapeamentoBW() {
  const [abaAtiva, setAbaAtiva] = useState('dashboard');
  const [queries, setQueries] = useState(
    QUERIES_INICIAIS.map(q => ({
      ...q,
      tabelas: '',
      qtdTabelas: 0,
      replicadaHana: '',
      complexidade: '',
      volumetria: '',
      esforcoHana: 0,
      esforcoGcp: 0,
      observacoes: ''
    }))
  );
  
  const [tabelas, setTabelas] = useState([]);
  const [custos, setCustos] = useState({
    hanaProjeto: 0,
    hanaRecorrente: 0,
    gcpProjeto: 0,
    gcpStorage: 0,
    gcpCompute: 0,
    incentivoPSF: 0,
    incentivoGoogle: 0
  });

  const atualizarQuery = (id, campo, valor) => {
    setQueries(queries.map(q => {
      if (q.id === id) {
        const updated = { ...q, [campo]: valor };
        if (campo === 'tabelas') {
          updated.qtdTabelas = valor ? valor.split(',').filter(t => t.trim()).length : 0;
        }
        return updated;
      }
      return q;
    }));
  };

  const adicionarTabela = () => {
    setTabelas([...tabelas, {
      id: Date.now(),
      nome: '',
      usadaPor: '',
      replicadaHana: 'nao',
      volumetria: '',
      frequencia: '',
      prioridade: 'media'
    }]);
  };

  const atualizarTabela = (id, campo, valor) => {
    setTabelas(tabelas.map(t => t.id === id ? { ...t, [campo]: valor } : t));
  };

  const removerTabela = (id) => {
    setTabelas(tabelas.filter(t => t.id !== id));
  };

  // Cálculos automáticos
  const metricas = useMemo(() => {
    const totalQueries = queries.length;
    const queriesMapeadas = queries.filter(q => q.tabelas).length;
    const replicadasSim = queries.filter(q => q.replicadaHana === 'sim').length;
    const replicadasNao = queries.filter(q => q.replicadaHana === 'nao').length;
    const replicadasParcial = queries.filter(q => q.replicadaHana === 'parcial').length;
    const complexidadeAlta = queries.filter(q => q.complexidade === 'alta').length;
    const totalEsforcoHana = queries.reduce((sum, q) => sum + (parseFloat(q.esforcoHana) || 0), 0);
    const totalEsforcoGcp = queries.reduce((sum, q) => sum + (parseFloat(q.esforcoGcp) || 0), 0);
    
    const tabelasUnicas = new Set();
    queries.forEach(q => {
      if (q.tabelas) {
        q.tabelas.split(',').forEach(t => {
          const nome = t.trim();
          if (nome) tabelasUnicas.add(nome);
        });
      }
    });
    
    const tabelasReplicadasHana = tabelas.filter(t => t.replicadaHana === 'sim').length;
    const tabelasPendentes = tabelas.filter(t => t.replicadaHana === 'nao').length;
    
    const custoTotalHana = custos.hanaProjeto + (custos.hanaRecorrente * 12);
    const custoTotalGcp = custos.gcpProjeto + ((custos.gcpStorage + custos.gcpCompute) * 12) - custos.incentivoPSF - custos.incentivoGoogle;
    
    return {
      totalQueries,
      queriesMapeadas,
      percMapeamento: totalQueries > 0 ? (queriesMapeadas / totalQueries * 100).toFixed(1) : 0,
      replicadasSim,
      replicadasNao,
      replicadasParcial,
      percReplicadas: replicadasSim > 0 ? (replicadasSim / totalQueries * 100).toFixed(1) : 0,
      complexidadeAlta,
      totalEsforcoHana: totalEsforcoHana.toFixed(1),
      totalEsforcoGcp: totalEsforcoGcp.toFixed(1),
      tabelasUnicas: tabelasUnicas.size,
      tabelasReplicadasHana,
      tabelasPendentes,
      percTabelasReplicadas: tabelas.length > 0 ? (tabelasReplicadasHana / tabelas.length * 100).toFixed(1) : 0,
      custoTotalHana: custoTotalHana.toFixed(2),
      custoTotalGcp: custoTotalGcp.toFixed(2),
      economiaGcp: (custoTotalHana - custoTotalGcp).toFixed(2)
    };
  }, [queries, tabelas, custos]);

  const dadosGraficoReplicacao = [
    { name: 'Replicadas', value: metricas.replicadasSim, color: '#10b981' },
    { name: 'Parciais', value: metricas.replicadasParcial, color: '#f59e0b' },
    { name: 'Não Replicadas', value: metricas.replicadasNao, color: '#ef4444' },
    { name: 'Não Mapeadas', value: metricas.totalQueries - metricas.queriesMapeadas, color: '#94a3b8' }
  ];

  const dadosGraficoEsforco = [
    { cenario: 'HANA', horas: parseFloat(metricas.totalEsforcoHana) },
    { cenario: 'GCP', horas: parseFloat(metricas.totalEsforcoGcp) }
  ];

  const dadosGraficoCusto = [
    { cenario: 'HANA', custo: parseFloat(metricas.custoTotalHana) },
    { cenario: 'GCP', custo: parseFloat(metricas.custoTotalGcp) }
  ];

  const exportarCSV = () => {
    const headers = ['Query ID', 'Nome', 'Área', 'Tabelas', 'Qtd Tabelas', 'Replicada HANA', 'Complexidade', 'Volumetria', 'Esforço HANA (h)', 'Esforço GCP (h)', 'Observações'];
    const rows = queries.map(q => [
      q.id, q.nome, q.area, q.tabelas, q.qtdTabelas, q.replicadaHana, q.complexidade, q.volumetria, q.esforcoHana, q.esforcoGcp, q.observacoes
    ]);
    
    const csv = [headers, ...rows].map(row => row.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'mapeamento_bw_queries.csv';
    a.click();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-slate-800 mb-2">Mapeamento BW - Migração SRM</h1>
              <p className="text-slate-600">Análise Comparativa: SAP HANA vs Google Cloud Platform</p>
            </div>
            <button
              onClick={exportarCSV}
              className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Download size={20} />
              Exportar CSV
            </button>
          </div>
        </div>

        {/* Abas */}
        <div className="bg-white rounded-lg shadow-lg mb-6">
          <div className="flex border-b border-slate-200">
            {[
              { id: 'dashboard', label: '📊 Dashboard' },
              { id: 'queries', label: '🔍 Queries (26)' },
              { id: 'tabelas', label: '📋 Tabelas' },
              { id: 'custos', label: '💰 Custos' },
              { id: 'comparativo', label: '⚖️ Comparativo' }
            ].map(aba => (
              <button
                key={aba.id}
                onClick={() => setAbaAtiva(aba.id)}
                className={`px-6 py-3 font-medium transition-colors ${
                  abaAtiva === aba.id
                    ? 'border-b-2 border-blue-600 text-blue-600'
                    : 'text-slate-600 hover:text-slate-800'
                }`}
              >
                {aba.label}
              </button>
            ))}
          </div>
        </div>

        {/* Conteúdo das Abas */}
        <div className="space-y-6">
          {/* Dashboard */}
          {abaAtiva === 'dashboard' && (
            <>
              {/* Cards de Métricas */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-white rounded-lg shadow p-6">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-slate-600 text-sm">Progresso Mapeamento</span>
                    <CheckCircle className="text-blue-600" size={20} />
                  </div>
                  <div className="text-3xl font-bold text-slate-800">{metricas.percMapeamento}%</div>
                  <div className="text-sm text-slate-500 mt-1">{metricas.queriesMapeadas} de {metricas.totalQueries} queries</div>
                </div>

                <div className="bg-white rounded-lg shadow p-6">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-slate-600 text-sm">Replicadas HANA</span>
                    <TrendingUp className="text-green-600" size={20} />
                  </div>
                  <div className="text-3xl font-bold text-slate-800">{metricas.percReplicadas}%</div>
                  <div className="text-sm text-slate-500 mt-1">{metricas.replicadasSim} queries confirmadas</div>
                </div>

                <div className="bg-white rounded-lg shadow p-6">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-slate-600 text-sm">Tabelas Únicas</span>
                    <AlertCircle className="text-orange-600" size={20} />
                  </div>
                  <div className="text-3xl font-bold text-slate-800">{metricas.tabelasUnicas}</div>
                  <div className="text-sm text-slate-500 mt-1">{metricas.tabelasReplicadasHana} já no HANA ({metricas.percTabelasReplicadas}%)</div>
                </div>

                <div className="bg-white rounded-lg shadow p-6">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-slate-600 text-sm">Complexidade Alta</span>
                    <AlertCircle className="text-red-600" size={20} />
                  </div>
                  <div className="text-3xl font-bold text-slate-800">{metricas.complexidadeAlta}</div>
                  <div className="text-sm text-slate-500 mt-1">Queries críticas</div>
                </div>
              </div>

              {/* Gráficos */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-lg font-bold text-slate-800 mb-4">Status de Replicação HANA</h3>
                  <ResponsiveContainer width="100%" height={250}>
                    <PieChart>
                      <Pie
                        data={dadosGraficoReplicacao}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, value }) => `${name}: ${value}`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {dadosGraficoReplicacao.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>

                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-lg font-bold text-slate-800 mb-4">Esforço Estimado (Horas)</h3>
                  <ResponsiveContainer width="100%" height={250}>
                    <BarChart data={dadosGraficoEsforco}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="cenario" />
                      <YAxis />
                      <Tooltip />
                      <Bar dataKey="horas" fill="#3b82f6" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Alerta de Progresso */}
              {metricas.percMapeamento < 50 && (
                <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 rounded">
                  <div className="flex">
                    <AlertCircle className="text-yellow-400 mr-3" size={24} />
                    <div>
                      <h3 className="text-yellow-800 font-medium">Mapeamento em Andamento</h3>
                      <p className="text-yellow-700 text-sm mt-1">
                        Apenas {metricas.percMapeamento}% das queries foram mapeadas. Continue preenchendo a aba "Queries" para ter métricas mais precisas.
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}

          {/* Queries */}
          {abaAtiva === 'queries' && (
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-slate-50 border-b border-slate-200">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-slate-600 uppercase">#</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-slate-600 uppercase">Query</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-slate-600 uppercase">Tabelas SRM</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-slate-600 uppercase">Qtd</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-slate-600 uppercase">HANA</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-slate-600 uppercase">Complex.</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-slate-600 uppercase">Esf. HANA (h)</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-slate-600 uppercase">Esf. GCP (h)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200">
                    {queries.map(q => (
                      <tr key={q.id} className="hover:bg-slate-50">
                        <td className="px-4 py-3 text-sm text-slate-600">{q.id}</td>
                        <td className="px-4 py-3">
                          <div className="text-sm font-medium text-slate-800">{q.nome}</div>
                          <div className="text-xs text-slate-500">{q.area}</div>
                        </td>
                        <td className="px-4 py-3">
                          <input
                            type="text"
                            value={q.tabelas}
                            onChange={(e) => atualizarQuery(q.id, 'tabelas', e.target.value)}
                            placeholder="TAB1, TAB2, TAB3..."
                            className="w-full px-2 py-1 text-sm border border-slate-300 rounded focus:outline-none focus:border-blue-500"
                          />
                        </td>
                        <td className="px-4 py-3 text-sm text-slate-600 text-center">{q.qtdTabelas}</td>
                        <td className="px-4 py-3">
                          <select
                            value={q.replicadaHana}
                            onChange={(e) => atualizarQuery(q.id, 'replicadaHana', e.target.value)}
                            className="w-full px-2 py-1 text-sm border border-slate-300 rounded focus:outline-none focus:border-blue-500"
                          >
                            <option value="">-</option>
                            <option value="sim">✓ Sim</option>
                            <option value="parcial">~ Parcial</option>
                            <option value="nao">✗ Não</option>
                          </select>
                        </td>
                        <td className="px-4 py-3">
                          <select
                            value={q.complexidade}
                            onChange={(e) => atualizarQuery(q.id, 'complexidade', e.target.value)}
                            className="w-full px-2 py-1 text-sm border border-slate-300 rounded focus:outline-none focus:border-blue-500"
                          >
                            <option value="">-</option>
                            <option value="baixa">Baixa</option>
                            <option value="media">Média</option>
                            <option value="alta">Alta</option>
                          </select>
                        </td>
                        <td className="px-4 py-3">
                          <input
                            type="number"
                            value={q.esforcoHana}
                            onChange={(e) => atualizarQuery(q.id, 'esforcoHana', e.target.value)}
                            placeholder="0"
                            className="w-20 px-2 py-1 text-sm border border-slate-300 rounded focus:outline-none focus:border-blue-500"
                          />
                        </td>
                        <td className="px-4 py-3">
                          <input
                            type="number"
                            value={q.esforcoGcp}
                            onChange={(e) => atualizarQuery(q.id, 'esforcoGcp', e.target.value)}
                            placeholder="0"
                            className="w-20 px-2 py-1 text-sm border border-slate-300 rounded focus:outline-none focus:border-blue-500"
                          />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Tabelas */}
          {abaAtiva === 'tabelas' && (
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-bold text-slate-800">Inventário de Tabelas SRM Únicas</h3>
                <button
                  onClick={adicionarTabela}
                  className="flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
                >
                  <Plus size={20} />
                  Nova Tabela
                </button>
              </div>

              <div className="bg-white rounded-lg shadow overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-slate-50 border-b border-slate-200">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-slate-600 uppercase">Tabela SRM</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-slate-600 uppercase">Usada por (Query IDs)</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-slate-600 uppercase">Replicada HANA?</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-slate-600 uppercase">Volumetria</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-slate-600 uppercase">Frequência</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-slate-600 uppercase">Prioridade</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-slate-600 uppercase">Ações</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-200">
                      {tabelas.length === 0 ? (
                        <tr>
                          <td colSpan="7" className="px-4 py-8 text-center text-slate-500">
                            Nenhuma tabela adicionada. Clique em "Nova Tabela" para começar.
                          </td>
                        </tr>
                      ) : (
                        tabelas.map(t => (
                          <tr key={t.id} className="hover:bg-slate-50">
                            <td className="px-4 py-3">
                              <input
                                type="text"
                                value={t.nome}
                                onChange={(e) => atualizarTabela(t.id, 'nome', e.target.value)}
                                placeholder="Nome da tabela"
                                className="w-full px-2 py-1 text-sm border border-slate-300 rounded focus:outline-none focus:border-blue-500"
                              />
                            </td>
                            <td className="px-4 py-3">
                              <input
                                type="text"
                                value={t.usadaPor}
                                onChange={(e) => atualizarTabela(t.id, 'usadaPor', e.target.value)}
                                placeholder="1, 5, 12..."
                                className="w-full px-2 py-1 text-sm border border-slate-300 rounded focus:outline-none focus:border-blue-500"
                              />
                            </td>
                            <td className="px-4 py-3">
                              <select
                                value={t.replicadaHana}
                                onChange={(e) => atualizarTabela(t.id, 'replicadaHana', e.target.value)}
                                className="w-full px-2 py-1 text-sm border border-slate-300 rounded focus:outline-none focus:border-blue-500"
                              >
                                <option value="nao">Não</option>
                                <option value="sim">Sim</option>
                                <option value="parcial">Parcial</option>
                              </select>
                            </td>
                            <td className="px-4 py-3">
                              <input
                                type="text"
                                value={t.volumetria}
                                onChange={(e) => atualizarTabela(t.id, 'volumetria', e.target.value)}
                                placeholder="ex: 5GB"
                                className="w-full px-2 py-1 text-sm border border-slate-300 rounded focus:outline-none focus:border-blue-500"
                              />
                            </td>
                            <td className="px-4 py-3">
                              <select
                                value={t.frequencia}
                                onChange={(e) => atualizarTabela(t.id, 'frequencia', e.target.value)}
                                className="w-full px-2 py-1 text-sm border border-slate-300 rounded focus:outline-none focus:border-blue-500"
                              >
                                <option value="">-</option>
                                <option value="realtime">Real-time</option>
                                <option value="diaria">Diária</option>
                                <option value="semanal">Semanal</option>
                                <option value="mensal">Mensal</option>
                              </select>
                            </td>
                            <td className="px-4 py-3">
                              <select
                                value={t.prioridade}
                                onChange={(e) => atualizarTabela(t.id, 'prioridade', e.target.value)}
                                className="w-full px-2 py-1 text-sm border border-slate-300 rounded focus:outline-none focus:border-blue-500"
                              >
                                <option value="baixa">Baixa</option>
                                <option value="media">Média</option>
                                <option value="alta">Alta</option>
                              </select>
                            </td>
                            <td className="px-4 py-3">
                              <button
                                onClick={() => removerTabela(t.id)}
                                className="text-red-600 hover:text-red-800"
                              >
                                <Trash2 size={18} />
                              </button>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* Custos */}
          {abaAtiva === 'custos' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* HANA */}
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-xl font-bold text-slate-800 mb-4">💼 Cenário HANA</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">Custo do Projeto (R$)</label>
                    <input
                      type="number"
                      value={custos.hanaProjeto}
                      onChange={(e) => setCustos({...custos, hanaProjeto: parseFloat(e.target.value) || 0})}
                      placeholder="0"
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:border-blue-500"
                    />
                    <p className="text-xs text-slate-500 mt-1">Contrato Petronect pode cobrir</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">Custo Recorrente Mensal (R$)</label>
                    <input
                      type="number"
                      value={custos.hanaRecorrente}
                      onChange={(e) => setCustos({...custos, hanaRecorrente: parseFloat(e.target.value) || 0})}
                      placeholder="0"
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:border-blue-500"
                    />
                  </div>
                  <div className="pt-4 border-t border-slate-200">
                    <div className="flex justify-between text-sm mb-2">
                      <span className="text-slate-600">Custo Anual Projeto:</span>
                      <span className="font-medium">R$ {custos.hanaProjeto.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between text-sm mb-2">
                      <span className="text-slate-600">Custo Anual Recorrente:</span>
                      <span className="font-medium">R$ {(custos.hanaRecorrente * 12).toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between text-lg font-bold text-blue-600">
                      <span>Total Anual:</span>
                      <span>R$ {metricas.custoTotalHana}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* GCP */}
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-xl font-bold text-slate-800 mb-4">☁️ Cenário GCP</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">Custo do Projeto (R$)</label>
                    <input
                      type="number"
                      value={custos.gcpProjeto}
                      onChange={(e) => setCustos({...custos, gcpProjeto: parseFloat(e.target.value) || 0})}
                      placeholder="0"
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">Storage Mensal (R$)</label>
                    <input
                      type="number"
                      value={custos.gcpStorage}
                      onChange={(e) => setCustos({...custos, gcpStorage: parseFloat(e.target.value) || 0})}
                      placeholder="0"
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">Compute Mensal (R$)</label>
                    <input
                      type="number"
                      value={custos.gcpCompute}
                      onChange={(e) => setCustos({...custos, gcpCompute: parseFloat(e.target.value) || 0})}
                      placeholder="0"
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:border-blue-500"
                    />
                  </div>
                  <div className="bg-green-50 rounded-lg p-3">
                    <label className="block text-sm font-medium text-green-800 mb-1">Incentivo PSF (R$)</label>
                    <input
                      type="number"
                      value={custos.incentivoPSF}
                      onChange={(e) => setCustos({...custos, incentivoPSF: parseFloat(e.target.value) || 0})}
                      placeholder="0"
                      className="w-full px-3 py-2 border border-green-300 rounded-lg focus:outline-none focus:border-green-500"
                    />
                    <p className="text-xs text-green-600 mt-1">Pode pagar projeto todo</p>
                  </div>
                  <div className="bg-green-50 rounded-lg p-3">
                    <label className="block text-sm font-medium text-green-800 mb-1">Incentivo Google (R$)</label>
                    <input
                      type="number"
                      value={custos.incentivoGoogle}
                      onChange={(e) => setCustos({...custos, incentivoGoogle: parseFloat(e.target.value) || 0})}
                      placeholder="0"
                      className="w-full px-3 py-2 border border-green-300 rounded-lg focus:outline-none focus:border-green-500"
                    />
                  </div>
                  <div className="pt-4 border-t border-slate-200">
                    <div className="flex justify-between text-sm mb-2">
                      <span className="text-slate-600">Custo Bruto Anual:</span>
                      <span className="font-medium">R$ {(custos.gcpProjeto + (custos.gcpStorage + custos.gcpCompute) * 12).toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between text-sm mb-2 text-green-600">
                      <span>Incentivos:</span>
                      <span className="font-medium">- R$ {(custos.incentivoPSF + custos.incentivoGoogle).toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between text-lg font-bold text-blue-600">
                      <span>Total Líquido Anual:</span>
                      <span>R$ {metricas.custoTotalGcp}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Comparativo */}
          {abaAtiva === 'comparativo' && (
            <div className="space-y-6">
              {/* Resumo Executivo */}
              <div className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-lg shadow-lg p-6 text-white">
                <h3 className="text-2xl font-bold mb-4">📊 Resumo Executivo</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div>
                    <div className="text-sm opacity-90 mb-1">Diferença de Esforço</div>
                    <div className="text-3xl font-bold">
                      {(parseFloat(metricas.totalEsforcoGcp) - parseFloat(metricas.totalEsforcoHana)).toFixed(1)}h
                    </div>
                    <div className="text-sm opacity-75 mt-1">
                      {parseFloat(metricas.totalEsforcoGcp) > parseFloat(metricas.totalEsforcoHana) ? 'GCP requer mais' : 'HANA requer mais'}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm opacity-90 mb-1">Diferença de Custo Anual</div>
                    <div className="text-3xl font-bold">
                      R$ {Math.abs(parseFloat(metricas.economiaGcp)).toFixed(2)}
                    </div>
                    <div className="text-sm opacity-75 mt-1">
                      {parseFloat(metricas.economiaGcp) > 0 ? 'Economia com GCP' : 'Economia com HANA'}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm opacity-90 mb-1">Recomendação</div>
                    <div className="text-2xl font-bold">
                      {parseFloat(metricas.custoTotalGcp) < parseFloat(metricas.custoTotalHana) ? '☁️ GCP' : '💼 HANA'}
                    </div>
                    <div className="text-sm opacity-75 mt-1">Baseado em custo total</div>
                  </div>
                </div>
              </div>

              {/* Gráfico Comparativo de Custos */}
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-bold text-slate-800 mb-4">Comparativo de Custos Totais (Anual)</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={dadosGraficoCusto}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="cenario" />
                    <YAxis />
                    <Tooltip formatter={(value) => `R$ ${value.toFixed(2)}`} />
                    <Legend />
                    <Bar dataKey="custo" fill="#3b82f6" name="Custo Total (R$)" />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Tabela Comparativa Detalhada */}
              <div className="bg-white rounded-lg shadow overflow-hidden">
                <table className="w-full">
                  <thead className="bg-slate-50 border-b border-slate-200">
                    <tr>
                      <th className="px-6 py-4 text-left text-sm font-bold text-slate-700">Critério</th>
                      <th className="px-6 py-4 text-left text-sm font-bold text-slate-700">HANA</th>
                      <th className="px-6 py-4 text-left text-sm font-bold text-slate-700">GCP BigQuery</th>
                      <th className="px-6 py-4 text-left text-sm font-bold text-slate-700">Vantagem</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200">
                    <tr className="hover:bg-slate-50">
                      <td className="px-6 py-4 text-sm font-medium text-slate-800">Queries Mapeadas</td>
                      <td className="px-6 py-4 text-sm text-slate-600">{metricas.queriesMapeadas} / {metricas.totalQueries}</td>
                      <td className="px-6 py-4 text-sm text-slate-600">{metricas.queriesMapeadas} / {metricas.totalQueries}</td>
                      <td className="px-6 py-4 text-sm text-slate-600">Empate</td>
                    </tr>
                    <tr className="hover:bg-slate-50">
                      <td className="px-6 py-4 text-sm font-medium text-slate-800">Tabelas já Replicadas</td>
                      <td className="px-6 py-4 text-sm text-slate-600">{metricas.replicadasSim} queries ({metricas.percReplicadas}%)</td>
                      <td className="px-6 py-4 text-sm text-slate-600">0 (começar do zero)</td>
                      <td className="px-6 py-4 text-sm"><span className="px-2 py-1 bg-blue-100 text-blue-800 rounded">HANA</span></td>
                    </tr>
                    <tr className="hover:bg-slate-50">
                      <td className="px-6 py-4 text-sm font-medium text-slate-800">Esforço Total Estimado</td>
                      <td className="px-6 py-4 text-sm text-slate-600">{metricas.totalEsforcoHana} horas</td>
                      <td className="px-6 py-4 text-sm text-slate-600">{metricas.totalEsforcoGcp} horas</td>
                      <td className="px-6 py-4 text-sm">
                        <span className={`px-2 py-1 rounded ${
                          parseFloat(metricas.totalEsforcoHana) < parseFloat(metricas.totalEsforcoGcp)
                            ? 'bg-blue-100 text-blue-800'
                            : 'bg-green-100 text-green-800'
                        }`}>
                          {parseFloat(metricas.totalEsforcoHana) < parseFloat(metricas.totalEsforcoGcp) ? 'HANA' : 'GCP'}
                        </span>
                      </td>
                    </tr>
                    <tr className="hover:bg-slate-50">
                      <td className="px-6 py-4 text-sm font-medium text-slate-800">Custo Total Anual</td>
                      <td className="px-6 py-4 text-sm text-slate-600">R$ {metricas.custoTotalHana}</td>
                      <td className="px-6 py-4 text-sm text-slate-600">R$ {metricas.custoTotalGcp}</td>
                      <td className="px-6 py-4 text-sm">
                        <span className={`px-2 py-1 rounded ${
                          parseFloat(metricas.custoTotalHana) < parseFloat(metricas.custoTotalGcp)
                            ? 'bg-blue-100 text-blue-800'
                            : 'bg-green-100 text-green-800'
                        }`}>
                          {parseFloat(metricas.custoTotalHana) < parseFloat(metricas.custoTotalGcp) ? 'HANA' : 'GCP'}
                        </span>
                      </td>
                    </tr>
                    <tr className="hover:bg-slate-50">
                      <td className="px-6 py-4 text-sm font-medium text-slate-800">Contrato Existente</td>
                      <td className="px-6 py-4 text-sm text-green-600">✓ Sim (Petronect)</td>
                      <td className="px-6 py-4 text-sm text-slate-600">✗ Não</td>
                      <td className="px-6 py-4 text-sm"><span className="px-2 py-1 bg-blue-100 text-blue-800 rounded">HANA</span></td>
                    </tr>
                    <tr className="hover:bg-slate-50">
                      <td className="px-6 py-4 text-sm font-medium text-slate-800">Incentivos Disponíveis</td>
                      <td className="px-6 py-4 text-sm text-slate-600">✗ Não</td>
                      <td className="px-6 py-4 text-sm text-green-600">✓ PSF + Google</td>
                      <td className="px-6 py-4 text-sm"><span className="px-2 py-1 bg-green-100 text-green-800 rounded">GCP</span></td>
                    </tr>
                    <tr className="hover:bg-slate-50">
                      <td className="px-6 py-4 text-sm font-medium text-slate-800">Arquitetura Delta</td>
                      <td className="px-6 py-4 text-sm text-green-600">✓ Já estabelecida</td>
                      <td className="px-6 py-4 text-sm text-orange-600">A definir</td>
                      <td className="px-6 py-4 text-sm"><span className="px-2 py-1 bg-blue-100 text-blue-800 rounded">HANA</span></td>
                    </tr>
                    <tr className="hover:bg-slate-50">
                      <td className="px-6 py-4 text-sm font-medium text-slate-800">Escalabilidade</td>
                      <td className="px-6 py-4 text-sm text-slate-600">Limitada</td>
                      <td className="px-6 py-4 text-sm text-green-600">✓ Cloud nativa</td>
                      <td className="px-6 py-4 text-sm"><span className="px-2 py-1 bg-green-100 text-green-800 rounded">GCP</span></td>
                    </tr>
                  </tbody>
                </table>
              </div>

              {/* Análise SWOT */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-lg font-bold text-slate-800 mb-4">💼 HANA - Análise SWOT</h3>
                  <div className="space-y-4">
                    <div>
                      <h4 className="font-medium text-green-700 mb-2">✓ Forças</h4>
                      <ul className="text-sm text-slate-600 space-y-1 list-disc list-inside">
                        <li>Contrato vigente com Petronect</li>
                        <li>{metricas.percReplicadas}% queries com tabelas já replicadas</li>
                        <li>Infraestrutura conhecida pela equipe</li>
                        <li>Arquitetura de delta estabelecida</li>
                      </ul>
                    </div>
                    <div>
                      <h4 className="font-medium text-red-700 mb-2">✗ Fraquezas</h4>
                      <ul className="text-sm text-slate-600 space-y-1 list-disc list-inside">
                        <li>Escalabilidade limitada</li>
                        <li>Sem incentivos financeiros adicionais</li>
                        <li>Tecnologia on-premise</li>
                      </ul>
                    </div>
                  </div>
                </div>

                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-lg font-bold text-slate-800 mb-4">☁️ GCP - Análise SWOT</h3>
                  <div className="space-y-4">
                    <div>
                      <h4 className="font-medium text-green-700 mb-2">✓ Forças</h4>
                      <ul className="text-sm text-slate-600 space-y-1 list-disc list-inside">
                        <li>Incentivo PSF (pode pagar projeto)</li>
                        <li>Escalabilidade cloud nativa</li>
                        <li>Modernização da arquitetura</li>
                        <li>Possíveis incentivos adicionais do Google</li>
                      </ul>
                    </div>
                    <div>
                      <h4 className="font-medium text-red-700 mb-2">✗ Fraquezas</h4>
                      <ul className="text-sm text-slate-600 space-y-1 list-disc list-inside">
                        <li>Replicação total necessária (do zero)</li>
                        <li>Arquitetura de delta a ser definida</li>
                        <li>Maior esforço inicial estimado</li>
                        <li>Custos recorrentes de cloud</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}