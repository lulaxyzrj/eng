'use client';

import type { Custos, Metricas } from '@/types';

interface CustosTabProps {
  custos: Custos;
  setCustos: (custos: Custos) => void;
  metricas: Metricas;
}

export default function CustosTab({ custos, setCustos, metricas }: CustosTabProps) {
  return (
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
  );
}