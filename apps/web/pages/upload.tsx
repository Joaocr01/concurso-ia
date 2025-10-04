import React, { useState } from "react";
import axios from "axios";

const API = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export default function Upload() {
  const [content, setContent] = useState("");
  const [filename, setFilename] = useState("input.txt");
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");

  async function submitText() {
    setLoading(true);
    try {
      const res = await axios.post(`${API}/upload`, { filename, content });
      setMsg(JSON.stringify(res.data));
    } catch (e: any) {
      setMsg(e?.message || "Erro");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main style={{ padding: 24 }}>
      <h2>Upload de Texto</h2>
      <input value={filename} onChange={e => setFilename(e.target.value)} placeholder="nome do arquivo" />
      <br /><br />
      <textarea rows={12} cols={80} value={content} onChange={e => setContent(e.target.value)} placeholder="Cole o texto aqui..." />
      <br />
      <button onClick={submitText} disabled={loading || !content}>Enviar</button>
      <p>{msg}</p>
    </main>
  );
}