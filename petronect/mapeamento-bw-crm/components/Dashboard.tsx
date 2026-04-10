'use client';

import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { CheckCircle, AlertCircle, TrendingUp } from 'lucide-react';
import type { Metricas, Query } from '@/types';

interface DashboardProps {
  metricas: Metricas;
  queries: Query[];
}

export default function Dashboard({ metricas, queries }: DashboardProps) {
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

  return (
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

      {/* Alerta */}
      {parseFloat(metricas.percMapeamento) < 50 && (
        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 rounded">
          <div className="flex">
            <AlertCircle className="text-yellow-400 mr-3" size={24} />
            <div>
              <h3 className="text-yellow-800 font-medium">Mapeamento em Andamento</h3>
              <p className="text-yellow-700 text-sm mt-1">
                Apenas {metricas.percMapeamento}% das queries foram mapeadas. Continue preenchendo a aba &quot;Queries&quot; para ter métricas mais precisas.
              </p>
            </div>
          </div>
        </div>
      )}
    </>
  );
}