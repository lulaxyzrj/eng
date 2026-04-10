'use client';

import type { Query } from '@/types';

interface QueriesTabProps {
  queries: Query[];
  setQueries: (queries: Query[]) => void;
}

export default function QueriesTab({ queries, setQueries }: QueriesTabProps) {
  const atualizarQuery = (id: number, campo: keyof Query, valor: string | number) => {
    setQueries(queries.map(q => {
      if (q.id === id) {
        const updated = { ...q, [campo]: valor };
        if (campo === 'tabelas') {
          updated.qtdTabelas = valor ? String(valor).split(',').filter(t => t.trim()).length : 0;
        }
        return updated;
      }
      return q;
    }));
  };

  return (
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
                    onChange={(e) => atualizarQuery(q.id, 'esforcoHana', parseFloat(e.target.value) || 0)}
                    placeholder="0"
                    className="w-20 px-2 py-1 text-sm border border-slate-300 rounded focus:outline-none focus:border-blue-500"
                  />
                </td>
                <td className="px-4 py-3">
                  <input
                    type="number"
                    value={q.esforcoGcp}
                    onChange={(e) => atualizarQuery(q.id, 'esforcoGcp', parseFloat(e.target.value) || 0)}
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
  );
}