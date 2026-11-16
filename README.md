# Auricchio Market Intelligence — Observatório de Metais

Hub estático para organizar observatórios interativos de metais e preservar snapshots históricos das análises.

## Estrutura

- `index.html` — portal central.
- `metals.json` — catálogo e estado resumido dos metais.
- `assets/` — recursos compartilhados do portal.
- `tin/`, `copper/`, `zinc/`, `nickel/`, `tungsten/` — observatórios por metal.
- `<metal>/index.html` — versão atual daquele observatório.
- `<metal>/reports/AAAA-MM-DD.html` — snapshots históricos.
- `<metal>/sources/` — reservado para fontes, somente quando houver autorização de armazenamento/publicação.

## GitHub Pages

1. Crie um repositório no GitHub.
2. Envie todo o conteúdo desta pasta para a raiz do repositório.
3. No GitHub, abra **Settings → Pages**.
4. Em **Build and deployment**, selecione **Deploy from a branch**.
5. Escolha a branch `main` e a pasta `/ (root)`.
6. Salve.

O arquivo `.nojekyll` já está incluído.

## Fluxo para novo relatório

Exemplo para Estanho em 20/11/2026:

1. Gere o novo observatório HTML.
2. Salve uma cópia em `tin/reports/2026-11-20.html`.
3. Substitua `tin/index.html` pela nova versão atual.
4. Atualize `metals.json` com data, viés e leitura resumida.
5. Faça commit e push.

## Observação importante

GitHub Pages publica conteúdo na web. Não inclua documentos confidenciais ou relatórios licenciados de terceiros sem verificar as permissões de distribuição.


## Histórico por metal

Cada metal possui:

```text
metal/
├── index.html
├── history.html
├── reports.json
└── reports/
    └── AAAA-MM-DD.html
```

- `index.html` = observatório atual.
- `history.html` = página que lista os snapshots históricos.
- `reports.json` = catálogo do histórico daquele metal.
- `reports/AAAA-MM-DD.html` = snapshot permanente da análise daquele dia.

### Ao publicar um novo relatório

1. Substituir `metal/index.html` pelo observatório mais recente.
2. Adicionar uma cópia em `metal/reports/AAAA-MM-DD.html`.
3. Adicionar a nova entrada no topo de `metal/reports.json`.
4. Atualizar `metals.json` com data, viés, físico e nota.
5. Fazer o commit. O GitHub Pages atualiza automaticamente.

Nunca apagar snapshots anteriores apenas porque existe um relatório novo.


## Automação de novos observatórios

O repositório possui uma automação em GitHub Actions.

### Fluxo diário

1. Gere os HTMLs dos metais com o bloco `report-meta`.
2. No GitHub, abra a pasta `incoming/`.
3. Clique em **Add file → Upload files**.
4. Envie um ou vários HTMLs.
5. Faça um único commit.

A automação processa cada HTML e:

- salva o snapshot em `metal/reports/AAAA-MM-DD.html`;
- substitui `metal/index.html` pela versão mais recente enviada;
- atualiza `metal/reports.json`;
- atualiza `metals.json`;
- remove o arquivo processado de `incoming/`;
- cria um commit automático.

### Permissão necessária

O workflow usa `permissions: contents: write`.

Se o GitHub bloquear o commit automático:

1. abra **Settings → Actions → General**;
2. vá até **Workflow permissions**;
3. marque **Read and write permissions**;
4. salve.

O GitHub também permite definir permissões no próprio workflow, mas configurações do repositório ou da organização podem restringir esse acesso.

Veja `REPORT_METADATA.md` para o formato obrigatório dos metadados.
