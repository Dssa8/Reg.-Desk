import cpflLogo from "./assets/cpfl.png";
import fsetLogo from "./assets/fset.png";
import users from "./data/users.json";

// Login (demo) baseado na aba 12_users do Excel: usuário = e-mail, senha = coluna "senha".
// A empresa (empresa_id) define o nome e a logo mostrados em "Preparado para".
//
// ⚠️ Continua sendo demonstração: as credenciais ficam no bundle do navegador,
// portanto NÃO são seguras. Para produção, mover a autenticação para o backend.

// empresa_id -> logo local
const LOGO_BY_COMPANY = {
  "1": fsetLogo,
  "2": cpflLogo,
};

function toClient(user) {
  if (!user) return null;
  return {
    id: user.companyId,
    name: user.companyName,
    logo: LOGO_BY_COMPANY[user.companyId] || fsetLogo,
    username: user.username,
  };
}

export function authenticate(username, password) {
  const user = (username || "").trim().toLowerCase();
  const found = users.find(
    (u) => u.username.toLowerCase() === user && u.password === password
  );
  return toClient(found);
}

// Restaura o cliente a partir do empresa_id salvo no localStorage.
export function getClientById(companyId) {
  if (!companyId) return null;
  return toClient(users.find((u) => u.companyId === companyId));
}
