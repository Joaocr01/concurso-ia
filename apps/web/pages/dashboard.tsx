import useSWR from "swr";
import axios from "axios";

const API = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
const fetcher = (url: string) => axios.get(url).then(r => r.data);

export default function Dashboard() {
  const { data, error } = useSWR(`${API}/questions?limit=20`, fetcher, { refreshInterval: 4000 });

  if (error) return <div>Erro ao carregar</div>;
  if (!data) return <div>Carregando...</div>;

  return (
    <main style={{ padding: 24 }}>
      <h2>Questões recentes</h2>
      <ul>
        {data.questions?.map((q: any) => (
          <li key={q.id} style={{marginBottom: 12}}>
            <strong>{q.title || "Sem título"}</strong><br/>
            <em>{q.enunciado}</em>
            <div style={{marginTop: 4}}>
              {Object.entries(q.alternatives).map(([k, v]: any) => (
                <div key={k}>{k}) {v}</div>
              ))}
            </div>
            <small>Correta: {q.correct_option} | Dificuldade: {q.difficulty} | Confiança: {q.confidence} | Cat: {q.category_name || "-"}</small>
          </li>
        ))}
      </ul>
    </main>
  );
}