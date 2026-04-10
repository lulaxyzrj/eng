'use client';

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import type { Metricas } from '@/types';

interface ComparativoTabProps {
  metricas: Metricas;
}

export default function ComparativoTab({ metricas }: ComparativoTabProps) {
  const dadosGraficoCusto = [
    { cenario: 'HANA', custo: parseFloat(metricas.custoTotalHana) },
    { cenario: 'GCP', custo: parseFloat(metricas.custoTotalGcp) }
  ];

  return (
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

      {/* Gráfico Comparativo */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-bold text-slate-800 mb-4">Comparativo de Custos Totais (Anual)</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={dadosGraficoCusto}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="cenario" />
            <YAxis />
            <Tooltip formatter={(value) => `R$ ${Number(value).toFixed(2)}`} />
            <Legend />
            <Bar dataKey="custo" fill="#3b82f6" name="Custo Total (R$)" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Tabela Comparativa */}
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
  );
}