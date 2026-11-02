import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AppShell from '../components/AppShell';
import Icon from '../components/Icon';
import { api } from '../services/api';

const DOCUMENT_TYPES = ['PDF', 'JPG', 'PNG'];

const emptyForm = {
  category: '',
  valid_from: '',
  valid_until: '',
  max_hours: '',
  accepted_document_types: [],
  confidence_threshold: '85',
  allows_auto_approval: false,
};

const hourFormat = value => Number(value).toLocaleString('pt-BR', { maximumFractionDigits: 2 });

const periodLabel = rule => {
  const start = new Date(`${rule.valid_from}T00:00:00`).toLocaleDateString('pt-BR');
  if (!rule.valid_until) return `${start} em diante`;
  const end = new Date(`${rule.valid_until}T00:00:00`).toLocaleDateString('pt-BR');
  return `${start} a ${end}`;
};

const errorText = (err, fallback) => {
  const detail = err.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail) && detail[0]?.msg) return String(detail[0].msg).replace(/^Value error, /, '');
  return fallback;
};

const toForm = rule => ({
  category: rule.category,
  valid_from: rule.valid_from,
  valid_until: rule.valid_until || '',
  max_hours: rule.max_hours == null ? '' : hourFormat(rule.max_hours),
  accepted_document_types: rule.accepted_document_types || [],
  confidence_threshold: String(Math.round(Number(rule.confidence_threshold) * 100)),
  allows_auto_approval: Boolean(rule.allows_auto_approval),
});

export default function AdminDashboard() {
  const navigate = useNavigate();
  const [rules, setRules] = useState([]);
  const [form, setForm] = useState(emptyForm);
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      navigate('/login');
      return;
    }

    const fetchRules = async () => {
      try {
        const response = await api.get('/rules', { headers: { Authorization: `Bearer ${token}` } });
        setRules(response.data);
      } catch {
        setError('Não foi possível carregar as regras. Atualize a página para tentar novamente.');
      } finally {
        setLoading(false);
      }
    };

    fetchRules();
  }, [navigate]);

  const today = new Date().toISOString().slice(0, 10);
  const autoCount = rules.filter(rule => rule.allows_auto_approval).length;
  const currentCount = rules.filter(rule => rule.valid_from <= today && (!rule.valid_until || rule.valid_until >= today)).length;
  const averageConfidence = rules.length
    ? Math.round(rules.reduce((sum, rule) => sum + Number(rule.confidence_threshold), 0) / rules.length * 100)
    : 0;

  const resetForm = () => {
    setEditingId(null);
    setForm(emptyForm);
    setError('');
    document.getElementById('rule-category')?.focus();
  };

  const toggleDocument = type => {
    setForm(current => ({
      ...current,
      accepted_document_types: current.accepted_document_types.includes(type)
        ? current.accepted_document_types.filter(item => item !== type)
        : [...current.accepted_document_types, type],
    }));
  };

  const handleSubmit = async event => {
    event.preventDefault();
    const hoursText = form.max_hours.trim();
    const hours = hoursText === '' ? null : Number(hoursText.replace(',', '.'));
    const confidence = Number(String(form.confidence_threshold).replace(',', '.'));
    if (hoursText !== '' && (!Number.isFinite(hours) || hours <= 0 || hours > 99999.99)) {
      setError('Informe uma carga horária máxima válida, como 40 ou 120,5.');
      return;
    }
    if (!Number.isFinite(confidence) || confidence < 0 || confidence > 100) {
      setError('O limite de confiança deve ficar entre 0 e 100.');
      return;
    }
    if (form.accepted_document_types.length === 0) {
      setError('Selecione ao menos um documento aceito.');
      return;
    }
    if (form.valid_until && form.valid_until < form.valid_from) {
      setError('O fim da vigência deve ser igual ou posterior ao início.');
      return;
    }

    setSaving(true);
    setError('');
    const token = localStorage.getItem('token');
    const payload = {
      category: form.category.trim(),
      valid_from: form.valid_from,
      valid_until: form.valid_until || null,
      max_hours: hours,
      accepted_document_types: form.accepted_document_types,
      confidence_threshold: confidence / 100,
      allows_auto_approval: form.allows_auto_approval,
    };
    try {
      if (editingId) {
        await api.put(`/rules/${editingId}`, payload, { headers: { Authorization: `Bearer ${token}` } });
      } else {
        await api.post('/rules', payload, { headers: { Authorization: `Bearer ${token}` } });
      }
    } catch (err) {
      setError(errorText(err, 'Não foi possível salvar a regra. Confira os campos e tente novamente.'));
      setSaving(false);
      return;
    }
    try {
      const response = await api.get('/rules', { headers: { Authorization: `Bearer ${token}` } });
      setRules(response.data);
      setEditingId(null);
      setForm(emptyForm);
    } catch {
      setError('A regra foi salva, mas a lista não pôde ser atualizada. Recarregue a página.');
    } finally {
      setSaving(false);
    }
  };

  return <AppShell title="Visão geral" variant="admin">
    <div className="page-heading"><div><span className="eyebrow">REGRAS DE VALIDAÇÃO</span><h1>Critérios para reconhecer o aprendizado.</h1><p>Cadastre e ajuste as regras que a aprovação automática vai consultar.</p></div><button className="btn-primary" type="button" onClick={resetForm}><Icon name="plus"/>Nova regra</button></div>
    {error && <div className="error-message" role="alert">{error}</div>}
    {loading ? <div className="loading-state" role="status"><span className="loading-spinner"/>Carregando as regras...</div> : <>
     <section className="stats-grid" aria-label="Resumo das regras">
      <div className="stat-card stat-featured"><div className="stat-top"><span>Regras cadastradas</span><Icon name="shield"/></div><strong className="stat-number">{rules.length.toString().padStart(2, '0')}</strong><span className="stat-caption">Critérios da instituição</span><div className="stat-decoration" aria-hidden="true"/></div>
      <div className="stat-card"><div className="stat-top"><span>Aprovação automática</span><span className="stat-icon approved"><Icon name="circleCheck"/></span></div><strong className="stat-number">{autoCount.toString().padStart(2, '0')}</strong><span className="stat-caption">Regras que dispensam análise manual</span></div>
      <div className="stat-card"><div className="stat-top"><span>Em vigência</span><span className="stat-icon pending"><Icon name="clock"/></span></div><strong className="stat-number">{currentCount.toString().padStart(2, '0')}</strong><span className="stat-caption">Válidas na data de hoje</span></div>
      <div className="stat-card"><div className="stat-top"><span>Confiança média</span><span className="stat-icon correction"><Icon name="edit"/></span></div><strong className="stat-number">{averageConfidence}<small>%</small></strong><span className="stat-caption">Limite médio das regras</span></div>
     </section>
     <div className="dashboard-lower rules-layout">
      <section className="panel requests-panel"><div className="panel-heading"><div><h2>Regras da instituição</h2><p>{rules.length} regra(s) para a aprovação automática</p></div></div>
       {rules.length === 0 ? <div className="empty-state"><span className="empty-icon"><Icon name="file" size={30}/></span><h3>Nenhuma regra cadastrada ainda.</h3><p>Defina a primeira categoria, o período e os documentos aceitos.</p><button className="btn-outline" type="button" onClick={resetForm}>Cadastrar primeira regra</button></div> : <div className="table-scroll"><table className="activity-table"><thead><tr><th>CATEGORIA</th><th>VIGÊNCIA</th><th>CARGA MÁX.</th><th>DOCUMENTOS</th><th>CONFIANÇA</th><th>AUTOMÁTICA</th><th><span className="sr-only">Ações</span></th></tr></thead><tbody>{rules.map(rule => <tr key={rule.id} className={editingId === rule.id ? 'is-selected' : ''}><td><div className="activity-name"><span className="file-icon"><Icon name="file"/></span><div><strong>{rule.category}</strong></div></div></td><td>{periodLabel(rule)}</td><td className="hours-cell">{rule.max_hours == null ? 'Sem limite' : `${hourFormat(rule.max_hours)} h`}</td><td>{(rule.accepted_document_types || []).join(', ')}</td><td className="hours-cell">{Math.round(Number(rule.confidence_threshold) * 100)}%</td><td><span className={`status-badge ${rule.allows_auto_approval ? 'approved' : 'draft'}`}>{rule.allows_auto_approval ? 'Permitida' : 'Manual'}</span></td><td><button type="button" className="table-action" onClick={() => { setEditingId(rule.id); setForm(toForm(rule)); setError(''); document.getElementById('rule-category')?.focus(); }}>Editar</button></td></tr>)}</tbody></table></div>}
       <div className="panel-footnote"><Icon name="shield" size={15}/><span>Esses critérios serão usados na aprovação automática dos documentos.</span></div>
      </section>
      <aside className="next-step"><div className="step-label"><span>{editingId ? 'EDITAR REGRA' : 'NOVA REGRA'}</span><Icon name={editingId ? 'edit' : 'plus'}/></div><h2>{editingId ? 'Ajuste os critérios desta categoria.' : 'Defina quando um documento pode seguir sozinho.'}</h2>
       <form id="rule-form" className="rule-form" onSubmit={handleSubmit}>
        <div className="form-group"><label htmlFor="rule-category">Categoria</label><input id="rule-category" type="text" maxLength={100} placeholder="Ex.: Curso de extensão" value={form.category} onChange={event => setForm({ ...form, category: event.target.value })} required/></div>
        <div className="form-group"><label htmlFor="rule-start">Início da vigência</label><input id="rule-start" type="date" value={form.valid_from} onChange={event => setForm({ ...form, valid_from: event.target.value })} required/></div>
        <div className="form-group"><label htmlFor="rule-end">Fim da vigência</label><input id="rule-end" type="date" min={form.valid_from || undefined} value={form.valid_until} onChange={event => setForm({ ...form, valid_until: event.target.value })}/></div>
        <div className="form-group"><label htmlFor="rule-hours">Carga horária máxima</label><div className="input-suffix"><input id="rule-hours" type="text" placeholder="Ex.: 40" inputMode="decimal" value={form.max_hours} onChange={event => setForm({ ...form, max_hours: event.target.value })}/><span>horas</span></div></div>
        <fieldset className="choice-fieldset"><legend>Documentos aceitos</legend><div className="choice-row">{DOCUMENT_TYPES.map(type => <label key={type}><input type="checkbox" checked={form.accepted_document_types.includes(type)} onChange={() => toggleDocument(type)}/>{type}</label>)}</div></fieldset>
        <div className="form-group"><label htmlFor="rule-confidence">Limite de confiança</label><div className="input-suffix"><input id="rule-confidence" type="number" min="0" max="100" step="1" value={form.confidence_threshold} onChange={event => setForm({ ...form, confidence_threshold: event.target.value })} required/><span>%</span></div></div>
        <label className="check-line"><input type="checkbox" checked={form.allows_auto_approval} onChange={event => setForm({ ...form, allows_auto_approval: event.target.checked })}/>Permite aprovação automática</label>
        <div className="rule-actions"><button type="submit" className="btn-primary" disabled={saving}>{saving ? 'Salvando...' : editingId ? 'Salvar alterações' : 'Cadastrar regra'}<Icon name="check" size={17}/></button>{editingId && <button type="button" className="btn-outline" disabled={saving} onClick={resetForm}>Cancelar edição</button>}</div>
       </form>
      </aside>
     </div>
     <section className="journey-strip" aria-label="Como as regras entram na validação"><div><span className="eyebrow">DA REGRA À APROVAÇÃO</span><h2>Um critério, um caminho.</h2></div><div className="journey-item"><span>01</span><div><strong>Categoria</strong><small>Ex.: curso de extensão.</small></div></div><div className="journey-item"><span>02</span><div><strong>Critérios</strong><small>Período, horas, documentos e confiança.</small></div></div><div className="journey-item"><span>03</span><div><strong>Automática</strong><small>Quando a regra permitir, o documento segue.</small></div></div></section>
    </>}
  </AppShell>;
}
