import React, { useState, useEffect, useRef, useMemo } from 'react';
import { 
  Network, 
  Share2, 
  Scale, 
  Search, 
  Filter, 
  Layers, 
  ExternalLink, 
  ShieldCheck, 
  CheckCircle2, 
  AlertTriangle, 
  TrendingUp, 
  Building2, 
  BookOpen, 
  Zap, 
  Maximize2, 
  RotateCcw, 
  Info, 
  FileText, 
  DollarSign,
  ChevronRight,
  X
} from 'lucide-react';
import { apiClient } from '../api/client';

export default function PrecedentsGraphView({ onSelectCase }) {
  const [graphData, setGraphData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState('ALL'); // ALL | retailer | precedent | legal_norm
  const [outcomeFilter, setOutcomeFilter] = useState('ALL'); // ALL | WON | PARTIAL_CONCESSION

  // Canvas Pan & Zoom
  const [transform, setTransform] = useState({ x: 0, y: 0, k: 0.95 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const containerRef = useRef(null);

  useEffect(() => {
    async function fetchGraph() {
      try {
        setLoading(true);
        const data = await apiClient.getPrecedentGraph();
        setGraphData(data);
      } catch (err) {
        console.error("Error loading precedent graph:", err);
        setError("No se pudo cargar la topología de la red de precedentes.");
      } finally {
        setLoading(false);
      }
    }
    fetchGraph();
  }, []);

  // Compute node coordinates deterministically in radial clusters
  const layoutNodes = useMemo(() => {
    if (!graphData || !graphData.nodes) return [];

    const nodes = graphData.nodes;
    const hub = nodes.find(n => n.type === 'hub') || { id: 'HUB_SUPPLYMIND', x: 500, y: 400 };
    const retailers = nodes.filter(n => n.type === 'retailer');
    const norms = nodes.filter(n => n.type === 'legal_norm');
    const precedents = nodes.filter(n => n.type === 'precedent');

    const WIDTH = 1000;
    const HEIGHT = 800;
    const CX = WIDTH / 2;
    const CY = HEIGHT / 2;

    const coords = new Map();
    coords.set(hub.id, { ...hub, x: CX, y: CY });

    // Place Legal Norms in an upper arc
    const normRadius = 190;
    norms.forEach((norm, idx) => {
      const angle = Math.PI * 0.15 + (idx / Math.max(1, norms.length - 1)) * Math.PI * 0.7;
      const x = CX + normRadius * Math.cos(angle - Math.PI);
      const y = CY + normRadius * Math.sin(angle - Math.PI) * 0.85;
      coords.set(norm.id, { ...norm, x, y });
    });

    // Place Retailers in an elliptical ring
    const retRadiusX = 330;
    const retRadiusY = 270;
    retailers.forEach((ret, idx) => {
      const angle = (idx / retailers.length) * 2 * Math.PI;
      const x = CX + retRadiusX * Math.cos(angle);
      const y = CY + retRadiusY * Math.sin(angle);
      coords.set(ret.id, { ...ret, x, y });
    });

    // Group precedents around their parent retailers
    const precedentsByRetailer = new Map();
    (graphData.links || []).forEach(link => {
      if (link.relation === 'DISPUTA_RESUELTA') {
        const pId = typeof link.target === 'object' ? link.target.id : link.target;
        const rId = typeof link.source === 'object' ? link.source.id : link.source;
        if (!precedentsByRetailer.has(rId)) precedentsByRetailer.set(rId, []);
        precedentsByRetailer.get(rId).push(pId);
      }
    });

    precedents.forEach((prec) => {
      // Find its retailer link
      let parentPos = { x: CX + (Math.random() - 0.5) * 400, y: CY + (Math.random() - 0.5) * 400 };
      let precIndex = 0;
      let totalSiblings = 1;

      for (const [rId, pList] of precedentsByRetailer.entries()) {
        const foundIdx = pList.indexOf(prec.id);
        if (foundIdx !== -1) {
          parentPos = coords.get(rId) || parentPos;
          precIndex = foundIdx;
          totalSiblings = pList.length;
          break;
        }
      }

      // Satellite offset around parent retailer
      const orbitDist = 65 + (precIndex % 2) * 25;
      const spreadAngle = (precIndex / Math.max(1, totalSiblings)) * 2 * Math.PI;
      const x = parentPos.x + orbitDist * Math.cos(spreadAngle);
      const y = parentPos.y + orbitDist * Math.sin(spreadAngle);

      coords.set(prec.id, { ...prec, x, y });
    });

    return Array.from(coords.values());
  }, [graphData]);

  const nodeMap = useMemo(() => {
    const map = new Map();
    layoutNodes.forEach(n => map.set(n.id, n));
    return map;
  }, [layoutNodes]);

  // Filtered nodes based on search & category
  const filteredNodes = useMemo(() => {
    return layoutNodes.filter(n => {
      if (typeFilter !== 'ALL' && n.type !== typeFilter) return false;
      if (outcomeFilter !== 'ALL' && n.type === 'precedent' && n.outcome !== outcomeFilter) return false;
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchLabel = n.label?.toLowerCase().includes(q);
        const matchSub = n.subtitle?.toLowerCase().includes(q);
        const matchCase = n.case_id?.toLowerCase().includes(q);
        const matchClause = n.governing_clause?.toLowerCase().includes(q);
        return matchLabel || matchSub || matchCase || matchClause;
      }
      return true;
    });
  }, [layoutNodes, typeFilter, outcomeFilter, searchQuery]);

  const filteredNodeIds = useMemo(() => new Set(filteredNodes.map(n => n.id)), [filteredNodes]);

  // Links connecting visible or selected nodes
  const visibleLinks = useMemo(() => {
    if (!graphData || !graphData.links) return [];
    return graphData.links.filter(l => {
      const sId = typeof l.source === 'object' ? l.source.id : l.source;
      const tId = typeof l.target === 'object' ? l.target.id : l.target;
      
      if (selectedNode) {
        // Highlight links connected to selected node
        return sId === selectedNode.id || tId === selectedNode.id;
      }
      return filteredNodeIds.has(sId) && filteredNodeIds.has(tId);
    });
  }, [graphData, filteredNodeIds, selectedNode]);

  // Pan / Drag handlers
  const handleMouseDown = (e) => {
    if (e.button !== 0) return;
    setIsDragging(true);
    setDragStart({ x: e.clientX - transform.x, y: e.clientY - transform.y });
  };

  const handleMouseMove = (e) => {
    if (!isDragging) return;
    setTransform(prev => ({
      ...prev,
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y
    }));
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleWheel = (e) => {
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.1 : 0.9;
    setTransform(prev => ({
      ...prev,
      k: Math.max(0.4, Math.min(2.5, prev.k * zoomFactor))
    }));
  };

  const handleResetView = () => {
    setTransform({ x: 0, y: 0, k: 0.95 });
    setSelectedNode(null);
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-96 space-y-3 font-mono text-zinc-400">
        <Network className="w-8 h-8 text-[#d4af37] animate-spin" />
        <span className="text-xs uppercase tracking-wider">Cargando Red de Memoria & Precedentes...</span>
      </div>
    );
  }

  if (error || !graphData) {
    return (
      <div className="p-8 text-center text-rose-400 font-mono text-xs ledger-card">
        <AlertTriangle className="w-8 h-8 mx-auto mb-2 text-rose-500" />
        <p>{error || "No hay datos de precedentes disponibles."}</p>
      </div>
    );
  }

  const { summary } = graphData;

  return (
    <div className="space-y-4 font-sans select-none">
      
      {/* 1. Header & Executive Metrics */}
      <div className="p-4 rounded-lg bg-[#101117] border border-[#1e202b] shadow-tactile flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-[10px] font-mono uppercase tracking-wider font-semibold px-2 py-0.5 rounded bg-[#1b1910] text-[#eed98d] border border-[#d4af37]/40">
              Red Neuronal de Precedentes B2B • Memoria SQLite
            </span>
            <span className="text-[10px] font-mono text-zinc-400">
              {summary.total_nodes} Nodos • {summary.total_links} Conexiones
            </span>
          </div>
          <h2 className="text-base font-bold text-white mt-1 flex items-center gap-2">
            <Network className="w-4 h-4 text-[#d4af37]" />
            <span>Topología Jurisprudencial & Perfiles de Retailer</span>
          </h2>
        </div>

        {/* Mini KPI badges */}
        <div className="flex flex-wrap items-center gap-2 font-mono text-xs">
          <div className="px-3 py-1.5 rounded bg-[#14151e] border border-[#232636]">
            <span className="text-[10px] text-zinc-500 uppercase block">Total Disputado</span>
            <span className="font-bold text-white">${Number(summary.total_disputed_usd).toLocaleString()} USD</span>
          </div>
          <div className="px-3 py-1.5 rounded bg-[#14151e] border border-emerald-900/50">
            <span className="text-[10px] text-emerald-400 uppercase block">Total Recuperado</span>
            <span className="font-bold text-emerald-300">${Number(summary.total_recovered_usd).toLocaleString()} USD</span>
          </div>
          <div className="px-3 py-1.5 rounded bg-[#14151e] border border-[#d4af37]/40">
            <span className="text-[10px] text-[#eed98d] uppercase block">Tasa de Acierto</span>
            <span className="font-bold text-[#eed98d]">{summary.global_recovery_rate_pct}%</span>
          </div>
        </div>
      </div>

      {/* 2. Controls & Filter Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-lg bg-[#0e0f14] border border-[#1d1f2b] text-xs font-mono">
        <div className="flex flex-wrap items-center gap-2 flex-1">
          {/* Search box */}
          <div className="relative min-w-[220px]">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-zinc-500" />
            <input
              type="text"
              placeholder="Buscar retailer, caso, norma..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-[#14161f] border border-[#252838] rounded pl-8 pr-3 py-1.5 text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-[#d4af37] text-xs"
            />
          </div>

          {/* Type Filter Buttons */}
          <div className="flex items-center space-x-1 bg-[#14161f] p-1 rounded border border-[#222533]">
            {['ALL', 'retailer', 'precedent', 'legal_norm'].map(type => (
              <button
                key={type}
                onClick={() => setTypeFilter(type)}
                className={`px-2 py-1 rounded text-[11px] transition-colors ${
                  typeFilter === type
                    ? 'bg-[#222533] text-white font-bold'
                    : 'text-zinc-400 hover:text-white'
                }`}
              >
                {type === 'ALL' && 'Todos'}
                {type === 'retailer' && '🏢 Retailers (37)'}
                {type === 'precedent' && '⚖️ Precedentes (59)'}
                {type === 'legal_norm' && '📜 Normas (6)'}
              </button>
            ))}
          </div>

          {/* Outcome Filter */}
          <div className="flex items-center space-x-1 bg-[#14161f] p-1 rounded border border-[#222533]">
            {['ALL', 'WON', 'PARTIAL_CONCESSION'].map(out => (
              <button
                key={out}
                onClick={() => setOutcomeFilter(out)}
                className={`px-2 py-1 rounded text-[11px] transition-colors ${
                  outcomeFilter === out
                    ? 'bg-[#222533] text-white font-bold'
                    : 'text-zinc-400 hover:text-white'
                }`}
              >
                {out === 'ALL' && 'Cualquier Fallo'}
                {out === 'WON' && '✅ 100% Ganados'}
                {out === 'PARTIAL_CONCESSION' && '🤝 Conciliados'}
              </button>
            ))}
          </div>
        </div>

        {/* View Controls */}
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setTransform(prev => ({ ...prev, k: Math.min(2.5, prev.k * 1.2) }))}
            className="p-1.5 rounded bg-[#14161f] hover:bg-[#1c1f2b] border border-[#252838] text-zinc-300"
            title="Acercar (+)"
          >
            +
          </button>
          <button
            onClick={() => setTransform(prev => ({ ...prev, k: Math.max(0.4, prev.k * 0.8) }))}
            className="p-1.5 rounded bg-[#14161f] hover:bg-[#1c1f2b] border border-[#252838] text-zinc-300"
            title="Alejar (-)"
          >
            -
          </button>
          <button
            onClick={handleResetView}
            className="px-2 py-1.5 rounded bg-[#14161f] hover:bg-[#1c1f2b] border border-[#252838] text-zinc-300 flex items-center space-x-1"
            title="Centrar y reiniciar vista"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset</span>
          </button>
        </div>
      </div>

      {/* 3. Interactive Topology Canvas / SVG */}
      <div className="relative rounded-lg bg-[#0a0b0f] border border-[#1b1c26] overflow-hidden h-[620px] shadow-2xl">
        
        {/* Background Grid Accent */}
        <div 
          className="absolute inset-0 opacity-15 pointer-events-none"
          style={{
            backgroundImage: 'radial-gradient(#d4af37 1px, transparent 1px)',
            backgroundSize: '32px 32px'
          }}
        />

        <svg
          ref={containerRef}
          className="w-full h-full cursor-grab active:cursor-grabbing"
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onWheel={handleWheel}
        >
          <g transform={`translate(${transform.x}, ${transform.y}) scale(${transform.k})`}>
            
            {/* Draw Links */}
            {visibleLinks.map((link, idx) => {
              const sNode = nodeMap.get(typeof link.source === 'object' ? link.source.id : link.source);
              const tNode = nodeMap.get(typeof link.target === 'object' ? link.target.id : link.target);
              if (!sNode || !tNode) return null;

              const isHighlighted = selectedNode && (sNode.id === selectedNode.id || tNode.id === selectedNode.id);

              return (
                <line
                  key={`link-${idx}`}
                  x1={sNode.x}
                  y1={sNode.y}
                  x2={tNode.x}
                  y2={tNode.y}
                  stroke={isHighlighted ? '#eed98d' : (link.color || 'rgba(150, 160, 180, 0.15)')}
                  strokeWidth={isHighlighted ? 2.5 : 1}
                  strokeDasharray={link.relation === 'AUDITA_CARTERA' ? '4 3' : 'none'}
                  opacity={isHighlighted ? 0.9 : 0.4}
                />
              );
            })}

            {/* Draw Nodes */}
            {layoutNodes.map((node) => {
              const isFiltered = filteredNodeIds.has(node.id);
              if (!isFiltered) return null;

              const isSelected = selectedNode?.id === node.id;
              const radius = node.radius || 12;

              return (
                <g
                  key={node.id}
                  transform={`translate(${node.x}, ${node.y})`}
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedNode(node);
                  }}
                  className="cursor-pointer transition-transform hover:scale-110"
                >
                  {/* Outer glow ring for selection or hub */}
                  {(isSelected || node.type === 'hub') && (
                    <circle
                      r={radius + 6}
                      fill="none"
                      stroke={node.color}
                      strokeWidth={1.5}
                      strokeDasharray={node.type === 'hub' ? '4 2' : 'none'}
                      opacity={0.7}
                      className={node.type === 'hub' ? 'animate-spin-slow' : ''}
                    />
                  )}

                  {/* Node Body */}
                  <circle
                    r={radius}
                    fill={node.color}
                    fillOpacity={node.type === 'hub' ? 0.9 : (isSelected ? 1.0 : 0.85)}
                    stroke="#0a0b0f"
                    strokeWidth={2}
                    className="shadow-lg"
                  />

                  {/* Inner Node Icon / Letter */}
                  <text
                    textAnchor="middle"
                    dy="0.35em"
                    fontSize={node.type === 'hub' ? '12px' : (node.type === 'precedent' ? '8px' : '10px')}
                    fontWeight="bold"
                    fill="#0a0b0f"
                    fontFamily="monospace"
                  >
                    {node.type === 'hub' && '⚖️'}
                    {node.type === 'retailer' && node.label?.substring(0, 2).toUpperCase()}
                    {node.type === 'legal_norm' && '§'}
                    {node.type === 'precedent' && (node.outcome === 'WON' ? '✓' : '•')}
                  </text>

                  {/* Text Label */}
                  <text
                    y={radius + 12}
                    textAnchor="middle"
                    fontSize={node.type === 'hub' ? '12px' : '9px'}
                    fontWeight={isSelected ? 'bold' : 'normal'}
                    fill={isSelected ? '#ffffff' : (node.type === 'hub' ? '#eed98d' : '#a1a1aa')}
                    fontFamily="monospace"
                    className="pointer-events-none drop-shadow"
                  >
                    {node.label}
                  </text>
                </g>
              );
            })}

          </g>
        </svg>

        {/* Legend Overlay */}
        <div className="absolute bottom-3 left-3 p-2.5 rounded bg-[#0e0f14]/90 border border-[#202230] backdrop-blur font-mono text-[10px] text-zinc-400 space-y-1.5 shadow-lg">
          <div className="font-bold text-zinc-300 uppercase tracking-wider mb-1">Convenciones</div>
          <div className="flex items-center space-x-2">
            <span className="w-2.5 h-2.5 rounded-full bg-[#d4af37]" />
            <span>Hub Central SupplyMind</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="w-2.5 h-2.5 rounded-full bg-[#0071dc]" />
            <span>Retailer / Gran Cadena Comercial</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="w-2.5 h-2.5 rounded-full bg-[#10b981]" />
            <span>Precedente 100% Favorable (WON)</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="w-2.5 h-2.5 rounded-full bg-[#f59e0b]" />
            <span>Conciliación Parcial / Concesión</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="w-2.5 h-2.5 rounded-full bg-[#f43f5e]" />
            <span>Precedente Desestimado</span>
          </div>
        </div>

        {/* 4. Side Inspector Drawer for Selected Node */}
        {selectedNode && (
          <div className="absolute top-3 right-3 w-84 md:w-96 rounded-lg bg-[#11121a]/95 border border-[#2b2e3e] shadow-2xl backdrop-blur-md p-4 animate-in slide-in-from-right duration-150 font-sans z-20">
            <div className="flex items-start justify-between border-b border-[#222432] pb-3 mb-3">
              <div>
                <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded font-bold" style={{ backgroundColor: `${selectedNode.color}22`, color: selectedNode.color }}>
                  {selectedNode.type === 'hub' && 'Núcleo Central'}
                  {selectedNode.type === 'retailer' && 'Perfil de Retailer'}
                  {selectedNode.type === 'precedent' && 'Fallo Precedente Vinculante'}
                  {selectedNode.type === 'legal_norm' && 'Fundamento Jurídico / Norma'}
                </span>
                <h3 className="text-sm font-bold text-white mt-1 font-mono">{selectedNode.label}</h3>
                {selectedNode.subtitle && (
                  <p className="text-xs text-zinc-400 mt-0.5">{selectedNode.subtitle}</p>
                )}
              </div>
              <button
                onClick={() => setSelectedNode(null)}
                className="p-1 rounded hover:bg-[#1d1f2b] text-zinc-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Precedent Specific Details */}
            {selectedNode.type === 'precedent' && (
              <div className="space-y-3 font-mono text-xs">
                <div className="grid grid-cols-2 gap-2">
                  <div className="p-2 rounded bg-[#161822] border border-[#242738]">
                    <span className="text-[10px] text-zinc-500 uppercase block">Disputado</span>
                    <span className="font-bold text-white">${selectedNode.disputed_amount?.toLocaleString()} USD</span>
                  </div>
                  <div className="p-2 rounded bg-[#161822] border border-emerald-900/40">
                    <span className="text-[10px] text-emerald-400 uppercase block">Recuperado</span>
                    <span className="font-bold text-emerald-300">${selectedNode.recovered_amount?.toLocaleString()} USD</span>
                  </div>
                </div>

                <div className="p-2.5 rounded bg-[#161822] border border-[#242738] space-y-1">
                  <span className="text-[10px] text-[#eed98d] uppercase block font-bold">Cláusula Rectora:</span>
                  <p className="text-[11px] text-zinc-300 font-sans">{selectedNode.governing_clause}</p>
                </div>

                {selectedNode.binding_argument && (
                  <div className="p-2.5 rounded bg-[#161822] border border-[#242738] space-y-1">
                    <span className="text-[10px] text-emerald-400 uppercase block font-bold">Argumento Vinculante:</span>
                    <p className="text-[11px] text-zinc-300 font-sans leading-relaxed">{selectedNode.binding_argument}</p>
                  </div>
                )}

                {onSelectCase && selectedNode.case_id && (
                  <button
                    onClick={() => onSelectCase(selectedNode.case_id)}
                    className="w-full btn-tactile py-2 rounded bg-[#1f1d14] hover:bg-[#282518] border border-[#d4af37]/60 text-[#eed98d] font-bold text-xs uppercase tracking-wider flex items-center justify-center space-x-1.5 transition-colors"
                  >
                    <span>Inspeccionar Caso en Hoja Contable</span>
                    <ChevronRight className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            )}

            {/* Retailer Specific Details */}
            {selectedNode.type === 'retailer' && (
              <div className="space-y-3 font-mono text-xs">
                <div className="grid grid-cols-2 gap-2">
                  <div className="p-2 rounded bg-[#161822] border border-[#242738]">
                    <span className="text-[10px] text-zinc-500 uppercase block">Casos Registrados</span>
                    <span className="font-bold text-white">{selectedNode.cases_count} expedientes</span>
                  </div>
                  <div className="p-2 rounded bg-[#161822] border border-[#242738]">
                    <span className="text-[10px] text-[#eed98d] uppercase block">Tasa de Recuperación</span>
                    <span className="font-bold text-[#eed98d]">{selectedNode.recovery_rate_pct}%</span>
                  </div>
                </div>

                <div className="p-2.5 rounded bg-[#161822] border border-[#242738] space-y-1">
                  <span className="text-[10px] text-zinc-400 uppercase block">Volumen Recuperado Acumulado:</span>
                  <div className="text-base font-bold text-emerald-400 font-mono">
                    ${selectedNode.total_recovered_usd?.toLocaleString()} USD
                  </div>
                </div>

                <div className="text-[11px] text-zinc-400 font-sans leading-snug">
                  Haz clic en cualquiera de los nodos satélites que orbitan a este retailer para auditar las sentencias arbitrales individuales.
                </div>
              </div>
            )}

            {/* Legal Norm Specific Details */}
            {selectedNode.type === 'legal_norm' && (
              <div className="space-y-3 font-mono text-xs">
                <div className="p-2.5 rounded bg-[#161822] border border-[#242738] space-y-1">
                  <span className="text-[10px] text-[#eed98d] uppercase block font-bold">Doctrina Comercial:</span>
                  <p className="text-[11px] text-zinc-300 font-sans leading-relaxed">{selectedNode.subtitle}</p>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div className="p-2 rounded bg-[#161822] border border-[#242738]">
                    <span className="text-[10px] text-zinc-500 uppercase block">Precedentes Cita</span>
                    <span className="font-bold text-white">{selectedNode.precedents_count} resoluciones</span>
                  </div>
                  <div className="p-2 rounded bg-[#161822] border border-emerald-900/40">
                    <span className="text-[10px] text-emerald-400 uppercase block">Monto Protegido</span>
                    <span className="font-bold text-emerald-300">${selectedNode.recovered_usd?.toLocaleString()} USD</span>
                  </div>
                </div>
              </div>
            )}

            {/* Hub Specific Details */}
            {selectedNode.type === 'hub' && (
              <div className="space-y-3 font-mono text-xs">
                <p className="text-[11px] text-zinc-300 font-sans leading-relaxed">
                  SupplyMind AI mantiene una base de datos vectorial y relacional en SQLite con jurisprudencia de más de 50 disputas comerciales resueltas entre los principales retailers de México y Norteamérica.
                </p>
                <div className="p-2.5 rounded bg-[#161822] border border-[#242738] space-y-1">
                  <span className="text-[10px] text-[#eed98d] uppercase block font-bold">Volumen Histórico Conciliado:</span>
                  <div className="text-base font-bold text-white font-mono">
                    ${summary.total_disputed_usd?.toLocaleString()} USD
                  </div>
                </div>
              </div>
            )}

          </div>
        )}

      </div>

    </div>
  );
}
