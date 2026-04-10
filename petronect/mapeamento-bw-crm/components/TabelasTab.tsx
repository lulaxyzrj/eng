'use client';

import { Plus, Trash2 } from 'lucide-react';
import type { Tabela } from '@/types';

interface TabelasTabProps {
  tabelas: Tabela[];
  setTabelas: (tabelas: Tabela[]) => void;
}

export default function TabelasTab({ tabelas, setTabelas }: TabelasTabProps) {
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

  const atualizarTabela = (id: number, campo: keyof Tabela, valor: string) => {
    setTabelas(tabelas.map(t => t.id === id ? { ...t, [campo]: valor } : t));
  };

  const removerTabela = (id: number) => {
    setTabelas(tabelas.filter(t => t.id !== id));
  };

  return (
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
                  <td colSpan={7} className="px-4 py-8 text-center text-slate-500">
                    Nenhuma tabela adicionada. Clique em &quot;Nova Tabela&quot; para começar.
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
  );
}