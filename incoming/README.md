# Incoming

Envie aqui os observatórios HTML novos.

## Fluxo diário

1. Entre nesta pasta no GitHub.
2. Use **Add file → Upload files**.
3. Envie um ou vários HTMLs gerados pelo ChatGPT.
4. Faça um único commit.

Cada HTML deve conter um bloco de metadados:

```html
<script id="report-meta" type="application/json">
{
  "metal": "tin",
  "date": "2026-11-17",
  "title": "Título do relatório",
  "bias": "Bearish",
  "physical": "Apertado",
  "note": "Resumo curto da leitura."
}
</script>
```

Metais aceitos:
- tin
- copper
- zinc
- nickel
- tungsten

A automação:
- copia o HTML para o histórico;
- atualiza o `index.html` do metal;
- atualiza `reports.json`;
- atualiza `metals.json`;
- remove o arquivo processado da pasta `incoming`;
- cria um commit automático.
