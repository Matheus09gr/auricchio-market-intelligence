# Metadados obrigatórios dos observatórios

Todo HTML enviado para `incoming/` deve conter, antes de `</body>` ou em qualquer ponto do HTML, o seguinte bloco:

```html
<script id="report-meta" type="application/json">
{
  "metal": "tin",
  "date": "2026-11-17",
  "title": "Tin report title",
  "bias": "Bearish",
  "physical": "Apertado",
  "note": "Resumo curto para aparecer no portal."
}
</script>
```

## Campos

- `metal`: `tin`, `copper`, `zinc`, `nickel` ou `tungsten`.
- `date`: `AAAA-MM-DD`.
- `title`: título do research/análise.
- `bias`: leitura curta, por exemplo `Bearish`, `Neutral-bearish`, `Bullish`.
- `physical`: situação do físico, por exemplo `Apertado`, `Neutro`, `Folgado`, `Misto`.
- `note`: uma frase curta para o portal.

## Importante

O workflow recusa o arquivo se faltar qualquer campo obrigatório.
