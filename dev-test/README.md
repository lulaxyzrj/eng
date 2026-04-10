# Dev Test — Controle de Tarefas

## Aviso sobre a URL do repositório

**A URL deste repositório foi alterada em relação à que está indicada nos PDFs do teste.**  
Ao enviar a solução ou referenciar o projeto, utilize a URL atual do repositório (onde você clonou ou fez o fork), e não a que eventualmente conste nos documentos *"1 - Instruções para Realização do Teste.pdf"* ou *"2 - Especificação Funcional Controle Tarefas.pdf"*.

---

## Sobre o projeto

Projeto de **Controle de Tarefas** composto por:

- **Backend** (`dev-test-back/`): API REST em **Java 21** com **Spring Boot 3.4**, JPA, Spring Security e banco **H2**.
- **Frontend** (`dev-test-front/`): aplicação **Angular** (TypeScript) que consome a API.

A especificação funcional e as instruções do teste estão nos PDFs na raiz do repositório.

---

## Estrutura do repositório

| Pasta / arquivo | Descrição |
|-----------------|-----------|
| `1 - Instruções para Realização do Teste.pdf` | Instruções gerais do teste |
| `2 - Especificação Funcional Controle Tarefas.pdf` | Especificação funcional do sistema |
| `dev-test-back/` | Backend Spring Boot (API de tarefas) |
| `dev-test-front/` | Frontend Angular |

---

## Pré-requisitos

- **Backend:** [Java 21](https://www.oracle.com/br/java/technologies/downloads/), [Maven 3.x](https://maven.apache.org/download.cgi)
- **Frontend:** [Node.js](https://nodejs.org/) (recomendado LTS), NPM
- Git (cliente ou plugin na IDE)

---

## Como executar

### 1. Backend

```bash
cd dev-test-back
mvn spring-boot:run
```

A API ficará disponível em **http://localhost:8080**.  
Também é possível rodar pela IDE (classe principal: `DevTestApplication`).

### 2. Frontend

```bash
cd dev-test-front
npm install
npm run start
```

A aplicação sobe em **http://localhost:4200**.  
O `proxy.conf.json` redireciona as requisições para `/api` para o backend em `http://localhost:8080`, então é necessário ter o backend rodando para as chamadas à API funcionarem.

### Ordem recomendada

1. Subir o **backend** (porta 8080).  
2. Depois subir o **frontend** (porta 4200).  
3. Acessar **http://localhost:4200** no navegador.

---

## Informações adicionais para o exercício

- **Banco de dados:** H2 em memória; não é necessário instalar SGBD. A migration da tabela de tarefas está em `dev-test-back/db/migration/`.
- **Testes do backend:** `mvn test` dentro de `dev-test-back/`.
- **Documentação detalhada:** cada submódulo possui seu próprio `README.md` em `dev-test-back/` e `dev-test-front/` com orientações de ambiente e execução.
- Ao enviar a solução (por exemplo, link do repositório), use sempre a **URL atual** do repositório, e não a que possa estar citada nos PDFs.
