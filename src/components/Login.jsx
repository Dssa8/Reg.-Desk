import { useState } from "react";
import fsetLogo from "../assets/fset.png";
import { authenticate } from "../clients";

export default function Login({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const submit = (e) => {
    e.preventDefault();
    const client = authenticate(username, password);
    if (!client) {
      setError("E-mail ou senha inválidos.");
      return;
    }
    setError("");
    onLogin(client);
  };

  const inputClass =
    "font-body mt-1 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-[15px] text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-[#9FBE86] focus:bg-white";

  return (
    <div className="flex min-h-screen items-center justify-center bg-[linear-gradient(135deg,#3a5570_0%,#2b3f56_40%,#1f3145_72%,#16222e_100%)] p-6">
      <div className="w-full max-w-sm rounded-3xl border border-white/40 bg-white/85 p-8 shadow-2xl backdrop-blur-xl">
        <div className="flex items-center justify-center gap-1.5">
          <img src={fsetLogo} alt="FSET" className="h-10 w-auto shrink-0 object-contain" />

          <div className="min-w-0">
            <h1 className="font-heading relative top-[8px] text-[27px] leading-none tracking-tight text-[#2b3f56]">
              REGDESK
            </h1>
            <p className="font-body mt-1.5 text-[9px] uppercase tracking-[0.2em] text-slate-500">
              Inteligência Regulatória
            </p>
          </div>
        </div>

        <h2 className="font-heading mt-8 text-[18px] text-[#2b3f56]">Acessar painel</h2>
        <p className="font-body mt-1 text-[13px] text-slate-500">
          Entre com as credenciais do cliente.
        </p>

        <form onSubmit={submit} className="mt-6 space-y-4">
          <div>
            <label className="font-heading text-[11px] uppercase tracking-[0.14em] text-slate-500">
              E-mail
            </label>
            <input
              type="email"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoFocus
              autoComplete="username"
              placeholder="nome@empresa.com.br"
              className={inputClass}
            />
          </div>

          <div>
            <label className="font-heading text-[11px] uppercase tracking-[0.14em] text-slate-500">
              Senha
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              className={inputClass}
            />
          </div>

          {error && <p className="font-body text-[13px] text-red-600">{error}</p>}

          <button
            type="submit"
            className="font-heading w-full rounded-2xl bg-[#2b3f56] py-3 text-[15px] text-white transition hover:bg-[#3a5570]"
          >
            Entrar
          </button>
        </form>
      </div>
    </div>
  );
}
