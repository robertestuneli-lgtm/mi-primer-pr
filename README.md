# mi-primer-pr

Wecome to this practice repository! It exists so I can learn the full
Pull Request workflow: branch, commit, push, and open a PR on GitHub.

## What's here

- `greet.py`: a tiny script that prints a greeting.
- `forum_trends.py`: scraper que investiga tendencias en foros de
  inversion (Reddit) para ver de que se habla mas y usarlo como punto
  de partida para buscar empresas en las que investigar/invertir.

## Usage

```bash
python greet.py
```

### forum_trends.py

Analiza los posts "top" de subreddits de inversion (via el JSON
publico de Reddit, sin API key) y cuenta cuantas veces se menciona
cada ticker ($AAPL, TSLA, etc.), para detectar que empresas estan
generando mas conversacion.

```bash
python forum_trends.py
python forum_trends.py --subreddits wallstreetbets stocks investing
python forum_trends.py --time week --limit 100 --top 15
```

Salida: ranking de tickers por numero de menciones y score acumulado,
con ejemplos de titulos de posts donde aparecen.

**Importante:** esto mide popularidad/ruido en foros, no es una
recomendacion de inversion. Sirve como lista de candidatas a
investigar con analisis fundamental antes de decidir nada.
