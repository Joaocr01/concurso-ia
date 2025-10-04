import useSWR from "swr";
import axios from "axios";

const API = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
const fetcher = (url: string) => axios.get(url).then(r => r.data);

export default function Stats() {
  const { data, error } = useSWR(`${API}/attempts/stats`, fetcher, { refreshInterval: 5000 });

  if (error) return <div>Erro carregando estatísticas</div>;
  if (!data) return <div>Carregando...</div>;

  return (
    <main style={{ padding: 24 }}>
      <h2>Estatísticas</h2>
      <p>Total de tentativas: {data.total_attempts}</p>
      <p>Precisão geral: {data.accuracy}%</p>
      <h3>Por categoria</h3>
      <ul>
        {data.by_category?.map((c: any) => (
          <li key={c.category}>
            {c.category || "(sem categoria)"}: {c.corrects}/{c.attempts} ({c.accuracy_pct}%)
          </li>
        ))}
      </ul>
    </main>
  );
}