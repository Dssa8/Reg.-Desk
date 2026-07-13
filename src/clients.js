import cpflLogo from "./assets/cpfl.png";
import fsetLogo from "./assets/fset.png";

// Cadastro de clientes (demo). Cada cliente define a logo mostrada no header
// (abaixo de "Preparado para") e as credenciais de acesso.
//
// ⚠️ Login apenas para demonstração: as credenciais ficam no bundle do
// navegador, portanto NÃO são seguras. Para produção, mover a autenticação
// (e os dados por cliente) para o backend.
export const CLIENTS = [
  {
    id: "cpfl",
    name: "CPFL Energia",
    logo: cpflLogo,
    username: "cpfl",
    password: "cpfl2026",
  },
  {
    id: "fset",
    name: "FSET",
    logo: fsetLogo,
    username: "fset",
    password: "fset2026",
  },
];

export function authenticate(username, password) {
  const user = (username || "").trim().toLowerCase();
  return (
    CLIENTS.find((c) => c.username === user && c.password === password) || null
  );
}

export function getClientById(id) {
  return CLIENTS.find((c) => c.id === id) || null;
}
