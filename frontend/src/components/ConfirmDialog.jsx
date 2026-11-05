import { useEffect, useRef } from 'react';

export default function ConfirmDialog({ title, children, onConfirm, onCancel, busy = false }) {
  const dialog = useRef(null);
  useEffect(() => {
    const node = dialog.current;
    const previous = document.activeElement;
    node.showModal();
    return () => { node.close(); previous?.focus(); };
  }, []);
  return <dialog ref={dialog} aria-labelledby="confirmation-title" className="confirm-dialog"
    onCancel={event => { event.preventDefault(); if (!busy) onCancel(); }}>
    <h2 id="confirmation-title">{title}</h2><div>{children}</div>
    <div className="decision-actions"><button type="button" className="btn-outline" disabled={busy}
      autoFocus onClick={onCancel}>Voltar</button><button type="button" className="btn-primary"
      disabled={busy} aria-busy={busy} onClick={onConfirm}>{busy ? 'Salvando...' : 'Confirmar decisão'}</button></div>
  </dialog>;
}
