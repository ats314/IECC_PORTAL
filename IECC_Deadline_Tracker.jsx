import { useState, useMemo } from "react";

const DEADLINE = new Date("2026-04-30");
const TODAY = new Date("2026-03-05");
const DAYS_LEFT = Math.ceil((DEADLINE - TODAY) / (1000 * 60 * 60 * 24));

const PROPOSALS = [
  { id:"CECC1-26", proponent:"Holland, Bryan", track:"commercial", sg:"Commercial Administration Subgroup", sgRec:null, sgVote:null, caRec:null, caDate:null, needsSG:true, needsCC:true },
  { id:"CECP2-25", proponent:"Holland, Bryan", track:"commercial", sg:"Commercial Consensus Committee", sgRec:"AM", sgVote:"7-6", caRec:"Postponed", caDate:"2026-01-21", needsSG:false, needsCC:true },
  { id:"CECP4-25", proponent:"Rosenstock, Steven", track:"commercial", sg:"Commercial Consensus Committee", sgRec:"D", sgVote:"10-2-2", caRec:null, caDate:null, needsSG:false, needsCC:true },
  { id:"CECP5-25", proponent:"Johnson, Greg", track:"commercial", sg:"Commercial Modeling Subgroup", sgRec:"D", sgVote:"4-2-4", caRec:null, caDate:null, needsSG:false, needsCC:true },
  { id:"CECP7-25", proponent:"Swiecicki, Bruce", track:"commercial", sg:"Commercial Modeling Subgroup", sgRec:"AM", sgVote:"5-3-2", caRec:null, caDate:null, needsSG:false, needsCC:true },
  { id:"CECP9-25", proponent:"Rosenstock, Steven", track:"commercial", sg:"Commercial Modeling Subgroup", sgRec:null, sgVote:null, caRec:null, caDate:null, needsSG:true, needsCC:true },
  { id:"CEPC57-25", proponent:"Crandell, Jay", track:"commercial", sg:"Commercial Modeling Subgroup", sgRec:"D", sgVote:"7-0-4", caRec:null, caDate:null, needsSG:false, needsCC:true },
  { id:"RECC3-26", proponent:"(TBD)", track:"residential", sg:"Admin (SG1)", sgRec:null, sgVote:null, caRec:null, caDate:null, needsSG:true, needsCC:true },
  { id:"RECC4-26", proponent:"(TBD)", track:"residential", sg:"Admin (SG1)", sgRec:null, sgVote:null, caRec:null, caDate:null, needsSG:true, needsCC:true },
  { id:"RECC5-26", proponent:"(TBD)", track:"residential", sg:"Admin (SG1)", sgRec:null, sgVote:null, caRec:null, caDate:null, needsSG:true, needsCC:true },
  { id:"RECP17-25", proponent:"Rhodes, Tracee", track:"residential", sg:"Admin (SG1)", sgRec:"AS", sgVote:"4-3", caRec:null, caDate:null, needsSG:false, needsCC:true },
  { id:"IRCEPC1-25", proponent:"Rosenstock, Steven", track:"residential", sg:"EPLR (SG3)", sgRec:"AS", sgVote:"9-0-0", caRec:null, caDate:null, needsSG:false, needsCC:true },
  { id:"REPC3-25", proponent:"Farbman, Scott", track:"residential", sg:"EPLR (SG3)", sgRec:"AM", sgVote:"5-4", caRec:null, caDate:null, needsSG:false, needsCC:true },
  { id:"REPC54-25", proponent:"Rosenstock, Steven", track:"residential", sg:"EPLR (SG3)", sgRec:"AS", sgVote:"9-0-0", caRec:null, caDate:null, needsSG:false, needsCC:true },
  { id:"REPC55-25", proponent:"Rosenstock, Steven", track:"residential", sg:"EPLR (SG3)", sgRec:"AS", sgVote:"9-0-0", caRec:null, caDate:null, needsSG:false, needsCC:true },
  { id:"REPC64-25", proponent:"Beach, Denise", track:"residential", sg:"EPLR (SG3)", sgRec:"D", sgVote:"6-0-3", caRec:null, caDate:null, needsSG:false, needsCC:true },
  { id:"REPC65-25", proponent:"Sherman, Erin", track:"residential", sg:"EPLR (SG3)", sgRec:"AM", sgVote:"8-0-0", caRec:null, caDate:null, needsSG:false, needsCC:true },
  { id:"RECP13-26", proponent:"Schmidt, Amy", track:"residential", sg:"Envelope (SG4)", sgRec:"AS", sgVote:"9-6", caRec:null, caDate:null, needsSG:false, needsCC:true },
  { id:"RECP7-25", proponent:"Schmidt, Amy", track:"residential", sg:"Envelope (SG4)", sgRec:"D", sgVote:"9-6", caRec:null, caDate:null, needsSG:false, needsCC:true },
  { id:"REPC61-25", proponent:"Marston, Thomas", track:"residential", sg:"Existing Buildings (SG5)", sgRec:"AM", sgVote:null, caRec:null, caDate:null, needsSG:false, needsCC:true },
  { id:"RECP8-25", proponent:"Schwarz, Robert", track:"residential", sg:"HVACR (SG6)", sgRec:"D", sgVote:"7-3", caRec:null, caDate:null, needsSG:false, needsCC:true },
  { id:"REPC21-25", proponent:"Moore, Mike", track:"residential", sg:"HVACR (SG6)", sgRec:"AM", sgVote:"9-1", caRec:null, caDate:null, needsSG:false, needsCC:true },
  { id:"REPC22-25", proponent:"Moore, Mike", track:"residential", sg:"HVACR (SG6)", sgRec:"AM", sgVote:"11-0", caRec:null, caDate:null, needsSG:false, needsCC:true },
  { id:"REPC24-25", proponent:"Schwarz, Robert", track:"residential", sg:"HVACR (SG6)", sgRec:"No Motion", sgVote:null, caRec:"Postponed", caDate:"2026-02-25", needsSG:true, needsCC:true },
  { id:"REPC37-25", proponent:"Vijayakumar, Gayathri", track:"residential", sg:"HVACR (SG6)", sgRec:"D", sgVote:"9-2", caRec:"Postponed", caDate:"2026-02-25", needsSG:false, needsCC:true },
  { id:"REPC43-25", proponent:"Beach, Denise", track:"residential", sg:"HVACR (SG6)", sgRec:"D", sgVote:"9-0", caRec:"Postponed", caDate:"2026-02-25", needsSG:false, needsCC:true },
  { id:"REPC46-25", proponent:"Rosenstock, Steven", track:"residential", sg:"HVACR (SG6)", sgRec:"AM", sgVote:"11-0", caRec:null, caDate:null, needsSG:false, needsCC:true },
  { id:"REPC52-25", proponent:"Crandell, Jay", track:"residential", sg:"HVACR (SG6)", sgRec:"No Motion", sgVote:null, caRec:"Postponed", caDate:"2026-02-25", needsSG:true, needsCC:true },
  { id:"REPC53-25", proponent:"Kahre, Nathan", track:"residential", sg:"HVACR (SG6)", sgRec:"AS", sgVote:"8-0", caRec:"Remand", caDate:"2026-02-18", needsSG:true, needsCC:true },
  { id:"REPC53-25 Mod", proponent:"Kahre, Nathan", track:"residential", sg:"HVACR (SG6)", sgRec:"AM", sgVote:"12-0", caRec:"Remand", caDate:"2026-02-18", needsSG:false, needsCC:true },
  { id:"REPC67-25", proponent:"Deary, Tom", track:"residential", sg:"HVACR (SG6)", sgRec:null, sgVote:null, caRec:null, caDate:null, needsSG:true, needsCC:true },
  { id:"RECP12-25", proponent:"Vijayakumar, Gayathri", track:"residential", sg:"Modeling (SG2)", sgRec:"AS", sgVote:"7-3-2", caRec:"Remand", caDate:"2026-02-10", needsSG:true, needsCC:true },
  { id:"RECP15-25", proponent:"Rhodes, Tracee", track:"residential", sg:"Modeling (SG2)", sgRec:null, sgVote:null, caRec:null, caDate:null, needsSG:true, needsCC:true },
  { id:"RECP16-25", proponent:"Rosenstock, Steven", track:"residential", sg:"Modeling (SG2)", sgRec:null, sgVote:null, caRec:null, caDate:null, needsSG:true, needsCC:true },
  { id:"RECP20-25", proponent:"Tate, Eric", track:"residential", sg:"Modeling (SG2)", sgRec:null, sgVote:null, caRec:null, caDate:null, needsSG:true, needsCC:true },
  { id:"RECP21-25", proponent:"Tate, Eric", track:"residential", sg:"Modeling (SG2)", sgRec:null, sgVote:null, caRec:null, caDate:null, needsSG:true, needsCC:true },
  { id:"RECP22-25", proponent:"Tate, Eric", track:"residential", sg:"Modeling (SG2)", sgRec:null, sgVote:null, caRec:null, caDate:null, needsSG:true, needsCC:true },
  { id:"RECP3-25", proponent:"Vijayakumar, Gayathri", track:"residential", sg:"Modeling (SG2)", sgRec:"D", sgVote:"6-4", caRec:null, caDate:null, needsSG:false, needsCC:true },
  { id:"RECP9-25", proponent:"Rhodes, Tracee", track:"residential", sg:"Modeling (SG2)", sgRec:null, sgVote:null, caRec:null, caDate:null, needsSG:true, needsCC:true },
  { id:"REPC33-25", proponent:"Deary, Thomas", track:"residential", sg:"Modeling (SG2)", sgRec:null, sgVote:null, caRec:null, caDate:null, needsSG:true, needsCC:true },
  { id:"REPC34-25", proponent:"Heikkinen, Gary", track:"residential", sg:"Modeling (SG2)", sgRec:null, sgVote:null, caRec:null, caDate:null, needsSG:true, needsCC:true },
  { id:"REPC42-25", proponent:"Deary, Thomas", track:"residential", sg:"Modeling (SG2)", sgRec:null, sgVote:null, caRec:null, caDate:null, needsSG:true, needsCC:true },
  { id:"REPC49-25", proponent:"Swiecicki, Bruce", track:"residential", sg:"Modeling (SG2)", sgRec:null, sgVote:null, caRec:null, caDate:null, needsSG:true, needsCC:true },
];

const SG_MEETINGS = {
  commercial: {
    "Commercial Administration Subgroup": ["2026-03-12","2026-03-26","2026-04-07","2026-04-16","2026-04-21"],
    "Commercial Modeling Subgroup": ["2026-03-12","2026-03-26","2026-04-06","2026-04-16","2026-04-20"],
    "Commercial Consensus Committee": ["2026-03-11","2026-03-25","2026-04-22","2026-04-29"],
  },
  residential: {
    "Admin (SG1)": ["2026-04-29"],
    "EPLR (SG3)": ["2026-04-03","2026-04-13","2026-04-17","2026-04-27"],
    "Envelope (SG4)": ["2026-04-06","2026-04-29"],
    "Existing Buildings (SG5)": ["2026-03-12","2026-03-26","2026-04-16","2026-04-28"],
    "HVACR (SG6)": ["2026-03-23","2026-04-20"],
    "Modeling (SG2)": ["2026-03-24","2026-04-14","2026-04-28"],
    "Residential Consensus Committee": ["2026-03-05","2026-03-12","2026-03-19","2026-04-10","2026-04-23","2026-04-24","2026-04-30"],
  }
};

const CC_KEY = {commercial: "Commercial Consensus Committee", residential: "Residential Consensus Committee"};

function getRisk(p) {
  const sgMeetings = SG_MEETINGS[p.track]?.[p.sg] || [];
  const ccMeetings = SG_MEETINGS[p.track]?.[CC_KEY[p.track]] || [];
  const remainingSG = sgMeetings.filter(d => d >= "2026-03-05").length;
  const remainingCC = ccMeetings.filter(d => d >= "2026-03-05").length;

  if (p.needsSG && p.needsCC) {
    // Need SG vote first, then CC. Must have at least 1 SG meeting BEFORE last CC meeting
    const lastCC = ccMeetings[ccMeetings.length - 1];
    const sgBeforeLastCC = sgMeetings.filter(d => d >= "2026-03-05" && d < lastCC).length;
    if (sgBeforeLastCC === 0) return { level: "critical", reason: "No SG meeting before final CC", stepsLeft: 2, remainingSG, remainingCC };
    if (sgBeforeLastCC === 1) return { level: "high", reason: "Only 1 SG chance before CC deadline", stepsLeft: 2, remainingSG, remainingCC };
    return { level: "medium", reason: `${sgBeforeLastCC} SG meetings left, then CC`, stepsLeft: 2, remainingSG, remainingCC };
  }
  if (p.needsCC && !p.needsSG) {
    if (remainingCC === 0) return { level: "critical", reason: "No CC meetings left!", stepsLeft: 1, remainingSG, remainingCC };
    if (remainingCC === 1) return { level: "high", reason: "Last CC meeting only", stepsLeft: 1, remainingSG, remainingCC };
    return { level: "low", reason: `${remainingCC} CC meetings remaining`, stepsLeft: 1, remainingSG, remainingCC };
  }
  return { level: "low", reason: "On track", stepsLeft: 0, remainingSG, remainingCC };
}

const RISK_COLORS = { critical: "#dc2626", high: "#f59e0b", medium: "#3b82f6", low: "#22c55e" };
const RISK_BG = { critical: "#fef2f2", high: "#fffbeb", medium: "#eff6ff", low: "#f0fdf4" };
const TRACK_COLORS = { commercial: "#6366f1", residential: "#ec4899" };

export default function DeadlineTracker() {
  const [filter, setFilter] = useState("all");
  const [trackFilter, setTrackFilter] = useState("all");
  const [expandedSG, setExpandedSG] = useState(null);

  const enriched = useMemo(() => PROPOSALS.map(p => ({ ...p, risk: getRisk(p) })), []);

  const filtered = useMemo(() => {
    let f = enriched;
    if (filter !== "all") f = f.filter(p => p.risk.level === filter);
    if (trackFilter !== "all") f = f.filter(p => p.track === trackFilter);
    return f;
  }, [enriched, filter, trackFilter]);

  const grouped = useMemo(() => {
    const g = {};
    filtered.forEach(p => {
      if (!g[p.sg]) g[p.sg] = [];
      g[p.sg].push(p);
    });
    return Object.entries(g).sort((a, b) => {
      const aWorst = Math.min(...a[1].map(p => ["critical","high","medium","low"].indexOf(p.risk.level)));
      const bWorst = Math.min(...b[1].map(p => ["critical","high","medium","low"].indexOf(p.risk.level)));
      return aWorst - bWorst;
    });
  }, [filtered]);

  const counts = useMemo(() => ({
    critical: enriched.filter(p => p.risk.level === "critical").length,
    high: enriched.filter(p => p.risk.level === "high").length,
    medium: enriched.filter(p => p.risk.level === "medium").length,
    low: enriched.filter(p => p.risk.level === "low").length,
  }), [enriched]);

  const pctDone = useMemo(() => {
    const total = 510;
    const decided = total - PROPOSALS.length;
    return Math.round((decided / total) * 100);
  }, []);

  const deadlinePct = Math.max(0, Math.min(100, Math.round(((56 - DAYS_LEFT) / 56) * 100)));

  return (
    <div style={{ fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif", maxWidth: 960, margin: "0 auto", padding: 20, background: "#0f172a", minHeight: "100vh", color: "#e2e8f0" }}>
      {/* Header */}
      <div style={{ textAlign: "center", marginBottom: 32 }}>
        <div style={{ fontSize: 13, fontWeight: 600, letterSpacing: 2, color: "#94a3b8", textTransform: "uppercase" }}>IECC 2027 Secretariat</div>
        <h1 style={{ fontSize: 28, fontWeight: 700, margin: "8px 0", color: "#f1f5f9" }}>Deadline Risk Tracker</h1>
        <div style={{ fontSize: 14, color: "#64748b" }}>43 proposals remaining across 10 subgroups</div>
      </div>

      {/* Countdown + Progress */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16, marginBottom: 24 }}>
        <div style={{ background: "#1e293b", borderRadius: 12, padding: 20, textAlign: "center", border: "1px solid #334155" }}>
          <div style={{ fontSize: 42, fontWeight: 800, color: DAYS_LEFT <= 30 ? "#f59e0b" : "#22c55e" }}>{DAYS_LEFT}</div>
          <div style={{ fontSize: 13, color: "#94a3b8", marginTop: 4 }}>days to deadline</div>
          <div style={{ fontSize: 11, color: "#64748b", marginTop: 2 }}>April 30, 2026</div>
        </div>
        <div style={{ background: "#1e293b", borderRadius: 12, padding: 20, textAlign: "center", border: "1px solid #334155" }}>
          <div style={{ fontSize: 42, fontWeight: 800, color: "#6366f1" }}>{pctDone}%</div>
          <div style={{ fontSize: 13, color: "#94a3b8", marginTop: 4 }}>proposals decided</div>
          <div style={{ fontSize: 11, color: "#64748b", marginTop: 2 }}>{510 - PROPOSALS.length} of 510</div>
        </div>
        <div style={{ background: "#1e293b", borderRadius: 12, padding: 20, textAlign: "center", border: "1px solid #334155" }}>
          <div style={{ fontSize: 42, fontWeight: 800, color: counts.critical > 0 ? "#dc2626" : "#22c55e" }}>{counts.critical + counts.high}</div>
          <div style={{ fontSize: 13, color: "#94a3b8", marginTop: 4 }}>at risk proposals</div>
          <div style={{ fontSize: 11, color: "#64748b", marginTop: 2 }}>{counts.critical} critical, {counts.high} high</div>
        </div>
      </div>

      {/* Risk filter pills */}
      <div style={{ display: "flex", gap: 8, marginBottom: 16, flexWrap: "wrap", alignItems: "center" }}>
        <span style={{ fontSize: 12, color: "#64748b", marginRight: 4 }}>Risk:</span>
        {["all","critical","high","medium","low"].map(level => (
          <button key={level} onClick={() => setFilter(level)} style={{
            padding: "6px 14px", borderRadius: 20, border: filter === level ? "2px solid #e2e8f0" : "1px solid #334155",
            background: level === "all" ? (filter === "all" ? "#334155" : "#1e293b") : (filter === level ? RISK_COLORS[level]+"22" : "#1e293b"),
            color: level === "all" ? "#e2e8f0" : RISK_COLORS[level], cursor: "pointer", fontSize: 13, fontWeight: 600
          }}>
            {level === "all" ? `All (${PROPOSALS.length})` : `${level.charAt(0).toUpperCase()+level.slice(1)} (${counts[level]})`}
          </button>
        ))}
        <div style={{ flex: 1 }} />
        <span style={{ fontSize: 12, color: "#64748b", marginRight: 4 }}>Track:</span>
        {["all","commercial","residential"].map(t => (
          <button key={t} onClick={() => setTrackFilter(t)} style={{
            padding: "6px 14px", borderRadius: 20, border: trackFilter === t ? "2px solid #e2e8f0" : "1px solid #334155",
            background: trackFilter === t ? "#334155" : "#1e293b",
            color: t === "all" ? "#e2e8f0" : TRACK_COLORS[t], cursor: "pointer", fontSize: 13, fontWeight: 600
          }}>
            {t === "all" ? "Both" : t.charAt(0).toUpperCase()+t.slice(1)}
          </button>
        ))}
      </div>

      {/* Subgroup cards */}
      {grouped.map(([sg, proposals]) => {
        const worstRisk = proposals.reduce((w, p) => {
          const order = ["critical","high","medium","low"];
          return order.indexOf(p.risk.level) < order.indexOf(w) ? p.risk.level : w;
        }, "low");
        const isExpanded = expandedSG === sg;
        const track = proposals[0].track;
        const sgMeetingsLeft = (SG_MEETINGS[track]?.[sg] || []).filter(d => d >= "2026-03-05");
        const ccKey = CC_KEY[track];
        const ccMeetingsLeft = (SG_MEETINGS[track]?.[ccKey] || []).filter(d => d >= "2026-03-05");

        return (
          <div key={sg} style={{ background: "#1e293b", borderRadius: 12, marginBottom: 12, border: `1px solid ${RISK_COLORS[worstRisk]}33`, overflow: "hidden" }}>
            <div onClick={() => setExpandedSG(isExpanded ? null : sg)} style={{ padding: "16px 20px", cursor: "pointer", display: "flex", alignItems: "center", gap: 12 }}>
              <div style={{ width: 8, height: 8, borderRadius: "50%", background: RISK_COLORS[worstRisk], flexShrink: 0 }} />
              <div style={{ flex: 1 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <span style={{ fontWeight: 700, fontSize: 15 }}>{sg}</span>
                  <span style={{ fontSize: 11, padding: "2px 8px", borderRadius: 10, background: TRACK_COLORS[track]+"22", color: TRACK_COLORS[track], fontWeight: 600 }}>{track}</span>
                </div>
                <div style={{ fontSize: 12, color: "#94a3b8", marginTop: 4 }}>
                  {proposals.filter(p => p.needsSG).length > 0 && <span style={{ marginRight: 12 }}>{proposals.filter(p => p.needsSG).length} need SG vote</span>}
                  {sgMeetingsLeft.length > 0 && <span style={{ marginRight: 12 }}>{sgMeetingsLeft.length} SG mtg{sgMeetingsLeft.length !== 1 ? "s" : ""} left</span>}
                  <span>{ccMeetingsLeft.length} CC mtg{ccMeetingsLeft.length !== 1 ? "s" : ""} left</span>
                </div>
              </div>
              <div style={{ display: "flex", gap: 4 }}>
                {proposals.map(p => (
                  <div key={p.id} style={{ width: 10, height: 10, borderRadius: 2, background: RISK_COLORS[p.risk.level] }} title={p.id} />
                ))}
              </div>
              <div style={{ fontSize: 20, color: "#64748b", transform: isExpanded ? "rotate(180deg)" : "none", transition: "transform 0.2s" }}>&#9662;</div>
            </div>
            {isExpanded && (
              <div style={{ padding: "0 20px 16px" }}>
                {/* SG meeting timeline */}
                {sgMeetingsLeft.length > 0 && (
                  <div style={{ display: "flex", gap: 8, marginBottom: 12, flexWrap: "wrap" }}>
                    <span style={{ fontSize: 11, color: "#64748b", alignSelf: "center" }}>SG dates:</span>
                    {sgMeetingsLeft.map(d => (
                      <span key={d} style={{ fontSize: 11, padding: "3px 8px", borderRadius: 6, background: "#0f172a", color: "#94a3b8" }}>
                        {new Date(d+"T12:00:00").toLocaleDateString("en-US", {month:"short", day:"numeric"})}
                      </span>
                    ))}
                  </div>
                )}
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                  <thead>
                    <tr style={{ borderBottom: "1px solid #334155" }}>
                      <th style={{ textAlign: "left", padding: "8px 4px", color: "#64748b", fontWeight: 600 }}>Proposal</th>
                      <th style={{ textAlign: "left", padding: "8px 4px", color: "#64748b", fontWeight: 600 }}>Proponent</th>
                      <th style={{ textAlign: "center", padding: "8px 4px", color: "#64748b", fontWeight: 600 }}>SG Rec</th>
                      <th style={{ textAlign: "center", padding: "8px 4px", color: "#64748b", fontWeight: 600 }}>Steps</th>
                      <th style={{ textAlign: "left", padding: "8px 4px", color: "#64748b", fontWeight: 600 }}>Risk</th>
                    </tr>
                  </thead>
                  <tbody>
                    {proposals.sort((a,b) => ["critical","high","medium","low"].indexOf(a.risk.level) - ["critical","high","medium","low"].indexOf(b.risk.level)).map(p => (
                      <tr key={p.id} style={{ borderBottom: "1px solid #1e293b" }}>
                        <td style={{ padding: "10px 4px", fontWeight: 600, fontFamily: "monospace" }}>{p.id}</td>
                        <td style={{ padding: "10px 4px", color: "#94a3b8" }}>{p.proponent}</td>
                        <td style={{ padding: "10px 4px", textAlign: "center" }}>
                          {p.sgRec ? (
                            <span style={{ padding: "2px 8px", borderRadius: 6, fontSize: 11, fontWeight: 700,
                              background: p.sgRec.startsWith("A") ? "#22c55e22" : p.sgRec.startsWith("D") ? "#dc262622" : "#f59e0b22",
                              color: p.sgRec.startsWith("A") ? "#22c55e" : p.sgRec.startsWith("D") ? "#dc2626" : "#f59e0b"
                            }}>
                              {p.sgRec} {p.sgVote ? `(${p.sgVote})` : ""}
                            </span>
                          ) : <span style={{ color: "#475569" }}>---</span>}
                        </td>
                        <td style={{ padding: "10px 4px", textAlign: "center" }}>
                          <div style={{ display: "flex", justifyContent: "center", gap: 4 }}>
                            <div style={{ width: 20, height: 6, borderRadius: 3, background: p.needsSG ? "#475569" : "#22c55e" }} title={p.needsSG ? "SG vote needed" : "SG done"} />
                            <div style={{ width: 20, height: 6, borderRadius: 3, background: "#475569" }} title="CC vote needed" />
                          </div>
                        </td>
                        <td style={{ padding: "10px 4px" }}>
                          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                            <div style={{ width: 8, height: 8, borderRadius: "50%", background: RISK_COLORS[p.risk.level] }} />
                            <span style={{ fontSize: 11, color: RISK_COLORS[p.risk.level] }}>{p.risk.reason}</span>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        );
      })}

      {/* Footer */}
      <div style={{ textAlign: "center", marginTop: 32, padding: 16, fontSize: 11, color: "#475569" }}>
        IECC 2027 Secretariat Deadline Tracker — Data from iecc.db Session 22 — {TODAY.toLocaleDateString()}
      </div>
    </div>
  );
}