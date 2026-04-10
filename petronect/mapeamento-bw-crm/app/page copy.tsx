'use client';

import { useState, useMemo, useEffect } from 'react';  // ← useEffect aqui!
import { useState, useMemo } from 'react';
import Dashboard from '@/components/Dashboard';
import QueriesTab from '@/components/QueriesTab';
import TabelasTab from '@/components/TabelasTab';
import CustosTab from '@/components/CustosTab';
import ComparativoTab from '@/components/ComparativoTab';
import { Download } from 'lucide-react';
import type { Query, Tabela, Custos, Metricas } from '@/types';

<button
  onClick={() => {
    salvarDados('mapeamento-queries', queries);
    salvarDados('mapeamento-tabelas', tabelas);
    salvarDados('mapeamento-custos', custos);
    alert('✅ Dados salvos!');
  }}
  className="bg-green-600 text-white px-4 py-2 rounded-lg"
>
  💾 Salvar Dados
</button>

const QUERIES_INICIAIS: Omit<Query, 'tabelas' | 'qtdTabelas' | 'replicadaHana' | 'complexidade' | 'volumetria' | 'esforcoHana' | 'esforcoGcp' | 'observacoes'>[] = [
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
// Função auxiliar para salvar
function salvarDados(chave: string, dados: any) {
  if (typeof window !== 'undefined') {
    try {
      localStorage.setItem(chave, JSON.stringify(dados));
      console.log(`✅ Salvou ${chave}`); // Para debug
    } catch (error) {
      console.error('Erro ao salvar:', error);
    }
  }
}

// Função auxiliar para carregar
function carregarDados<T>(chave: string, padrao: T): T {
  if (typeof window !== 'undefined') {
    try {
      const item = localStorage.getItem(chave);
      if (item) {
        console.log(`✅ Carregou ${chave}`); // Para debug
        return JSON.parse(item);
      }
    } catch (error) {
      console.error('Erro ao carregar:', error);
    }
  }
  return padrao;
}

export default function Home() {
  const [abaAtiva, setAbaAtiva] = useState<string>('dashboard');
  
  const [queries, setQueries] = useState<Query[]>(() => 
    carregarDados('mapeamento-queries', QUERIES_INICIAIS.map(q => ({
      ...q,
      tabelas: '',
      qtdTabelas: 0,
      replicadaHana: '' as const,
      complexidade: '' as const,
      volumetria: '',
      esforcoHana: 0,
      esforcoGcp: 0,
      observacoes: ''
    })))
  );
  
  const [tabelas, setTabelas] = useState<Tabela[]>(() => 
    carregarDados('mapeamento-tabelas', [])
  );
  
  const [custos, setCustos] = useState<Custos>(() => 
    carregarDados('mapeamento-custos', {
      hanaProjeto: 0,
      hanaRecorrente: 0,
      gcpProjeto: 0,
      gcpStorage: 0,
      gcpCompute: 0,
      incentivoPSF: 0,
      incentivoGoogle: 0
    })
  );

  // Auto-save quando mudar
  useEffect(() => {
    salvarDados('mapeamento-queries', queries);
  }, [queries]);

  useEffect(() => {
    salvarDados('mapeamento-tabelas', tabelas);
  }, [tabelas]);

  useEffect(() => {
    salvarDados('mapeamento-custos', custos);
  }, [custos]);

  
 /* const [tabelas, setTabelas] = useState<Tabela[]>([]);
  const [custos, setCustos] = useState<Custos>({
    hanaProjeto: 0,
    hanaRecorrente: 0,
    gcpProjeto: 0,
    gcpStorage: 0,
    gcpCompute: 0,
    incentivoPSF: 0,
    incentivoGoogle: 0
  });
*/

  // Cálculos automáticos
  const metricas = useMemo<Metricas>(() => {
    const totalQueries = queries.length;
    const queriesMapeadas = queries.filter(q => q.tabelas).length;
    const replicadasSim = queries.filter(q => q.replicadaHana === 'sim').length;
    const replicadasNao = queries.filter(q => q.replicadaHana === 'nao').length;
    const replicadasParcial = queries.filter(q => q.replicadaHana === 'parcial').length;
    const complexidadeAlta = queries.filter(q => q.complexidade === 'alta').length;
    const totalEsforcoHana = queries.reduce((sum, q) => sum + (parseFloat(String(q.esforcoHana)) || 0), 0);
    const totalEsforcoGcp = queries.reduce((sum, q) => sum + (parseFloat(String(q.esforcoGcp)) || 0), 0);
    
    const tabelasUnicas = new Set<string>();
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
      percMapeamento: totalQueries > 0 ? (queriesMapeadas / totalQueries * 100).toFixed(1) : '0',
      replicadasSim,
      replicadasNao,
      replicadasParcial,
      percReplicadas: replicadasSim > 0 ? (replicadasSim / totalQueries * 100).toFixed(1) : '0',
      complexidadeAlta,
      totalEsforcoHana: totalEsforcoHana.toFixed(1),
      totalEsforcoGcp: totalEsforcoGcp.toFixed(1),
      tabelasUnicas: tabelasUnicas.size,
      tabelasReplicadasHana,
      tabelasPendentes,
      percTabelasReplicadas: tabelas.length > 0 ? (tabelasReplicadasHana / tabelas.length * 100).toFixed(1) : '0',
      custoTotalHana: custoTotalHana.toFixed(2),
      custoTotalGcp: custoTotalGcp.toFixed(2),
      economiaGcp: (custoTotalHana - custoTotalGcp).toFixed(2)
    };
  }, [queries, tabelas, custos]);

  const exportarCSV = () => {
    const headers = ['Query ID', 'Nome', 'Área', 'Tabelas', 'Qtd Tabelas', 'Replicada HANA', 'Complexidade', 'Volumetria', 'Esforço HANA (h)', 'Esforço GCP (h)', 'Observações'];
    const rows = queries.map(q => [
      q.id, q.nome, q.area, q.tabelas, q.qtdTabelas, q.replicadaHana, q.complexidade, q.volumetria, q.esforcoHana, q.esforcoGcp, q.observacoes
    ]);
    
    const csv = [headers, ...rows].map(row => row.join(',')).join('\n');
    const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'mapeamento_bw_queries.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              {/* Logo do Cliente */}
              <img src="/logo-cliente.jpeg" alt="Logo do Cliente" className="h-30" />
              <h1 className="text-3xl font-bold text-slate-800 mb-2">Mapeamento BW - Migração SRM</h1>
              <p className="text-slate-600">Análise Comparativa: SAP HANA vs GCP</p>
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
          <div className="flex border-b border-slate-200 overflow-x-auto">
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
                className={`px-6 py-3 font-medium transition-colors whitespace-nowrap ${
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

        {/* Conteúdo */}
        <div className="space-y-6">
          {abaAtiva === 'dashboard' && <Dashboard metricas={metricas} queries={queries} />}
          {abaAtiva === 'queries' && <QueriesTab queries={queries} setQueries={setQueries} />}
          {abaAtiva === 'tabelas' && <TabelasTab tabelas={tabelas} setTabelas={setTabelas} />}
          {abaAtiva === 'custos' && <CustosTab custos={custos} setCustos={setCustos} metricas={metricas} />}
          {abaAtiva === 'comparativo' && <ComparativoTab metricas={metricas} />}
        </div>
      </div>
    </div>
  );
}