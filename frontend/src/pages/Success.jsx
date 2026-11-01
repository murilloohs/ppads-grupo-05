import { useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import AppShell from '../components/AppShell';
import Icon from '../components/Icon';

export default function Success() {
  const navigate = useNavigate();
  const location = useLocation();

  const { protocol, formData, fileName } = location.state || {};

  useEffect(() => {
    if (!protocol) {
      navigate('/dashboard');
    }
  }, [protocol, navigate]);

  if (!protocol) return null;

  return <AppShell title="Solicitação enviada"><div className="success-layout"><section className="success-card"><div className="success-seal"><Icon name="check" size={34}/></div><span className="eyebrow">MAIS UM PASSO NO SEU PERCURSO</span><h1>Atividade enviada!</h1><p>Seu documento e sua solicitação foram recebidos.<br/>Agora você pode acompanhar o status pelo protocolo.</p><div className="protocol-ticket"><span>SEU PROTOCOLO</span><strong>{protocol}</strong><span className="status-badge pending">Em análise</span></div><div className="actions-group"><button className="btn-primary" onClick={()=>navigate('/minhas-solicitacoes')}>Minhas solicitações</button><button className="btn-outline" onClick={()=>navigate('/nova-atividade')}><Icon name="plus" size={17}/>Nova atividade</button></div></section><section className="panel receipt"><div className="panel-heading"><h2>Resumo do envio</h2><Icon name="file"/></div><dl><div><dt>Atividade</dt><dd>{formData?.nome}</dd></div><div><dt>Instituição promotora</dt><dd>{formData?.instituicao}</dd></div><div><dt>Categoria</dt><dd>{formData?.categoria}</dd></div><div><dt>Período</dt><dd>{formData?.periodo}</dd></div><div><dt>Carga horária</dt><dd>{formData?.cargaHoraria} horas</dd></div><div><dt>Documento</dt><dd>{fileName}</dd></div></dl><div className="receipt-note"><Icon name="clock" size={18}/><p>O envio não representa aprovação. Consulte o andamento em Minhas solicitações.</p></div></section></div></AppShell>;
}
