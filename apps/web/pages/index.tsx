import Link from "next/link";

export default function Home() {
  return (
    <main style={{padding: 24}}>
      <h1>Concurse AI</h1>
      <ul>
        <li><Link href="/upload">Upload de PDF/Texto</Link></li>
        <li><Link href="/dashboard">Dashboard</Link></li>
        <li><Link href="/stats">Estatísticas</Link></li>
      </ul>
    </main>
  );
}