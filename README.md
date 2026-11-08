# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.

## Authentication setup

The API requires a signing secret before it starts. Set a unique secret of at least 32 characters in the backend environment; do not commit it to source control. For local PowerShell development:

```powershell
$env:AUTH_SECRET_KEY = python -c "import secrets; print(secrets.token_urlsafe(48))"
Set-Location backend
uvicorn main:app --reload
```

Set `MONGO_URI` to the MongoDB connection string for the deployment. Clinician accounts are stored in the `pharm_ai_db.users` collection; passwords are stored as salted PBKDF2 hashes, and login retrieves the account by normalized email and verifies the submitted password. The API creates a unique email index to prevent duplicate accounts. Set `VITE_API_BASE_URL` in the frontend environment when using a backend other than the configured hosted API.

Accounts support Doctors, Nurses, and Health workers. Users can update their name and profession from the signed-in workspace; their email address cannot be changed through profile management. Passwords must be at least 12 characters. Access tokens expire after eight hours; clinical endpoints and per-account prediction history require a valid sign-in.
