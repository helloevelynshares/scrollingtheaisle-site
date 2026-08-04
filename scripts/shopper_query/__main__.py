"""Developer CLI / local HTTP harness for shopper-query experiment."""

from __future__ import annotations

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

SCRIPT_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from shopper_query.pipeline import process_query  # noqa: E402

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Shopper query harness (dev)</title>
  <style>
    body { font-family: ui-sans-serif, system-ui, sans-serif; margin: 2rem; max-width: 960px; }
    textarea { width: 100%; min-height: 80px; font-size: 1rem; }
    button { margin-right: 0.5rem; padding: 0.4rem 0.8rem; }
    pre { background: #f4f4f5; padding: 1rem; overflow: auto; font-size: 0.85rem; }
    .row { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
    label { display: flex; align-items: center; gap: 0.4rem; margin: 0.5rem 0; }
    h1 { font-size: 1.25rem; }
    .tag { display: inline-block; padding: 0.15rem 0.5rem; background: #e4e4e7; border-radius: 4px; }
  </style>
</head>
<body>
  <h1>Shopper query harness <span class="tag">dev / no LLM</span></h1>
  <p>Deterministic normalize → parse → production matcher. No deal verdict.</p>
  <textarea id="q" placeholder="e.g. Safeway Doritos 9.75 oz are 2 for five bucks when you buy 2"></textarea>
  <label><input type="checkbox" id="norm" checked /> Apply normalization layer</label>
  <div>
    <button id="run">Run</button>
  </div>
  <div class="row">
    <div>
      <h2>Summary</h2>
      <pre id="summary">—</pre>
    </div>
    <div>
      <h2>Full JSON</h2>
      <pre id="full">—</pre>
    </div>
  </div>
  <script>
    async function run() {
      const q = document.getElementById('q').value;
      const norm = document.getElementById('norm').checked;
      const res = await fetch('/api/query', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ query: q, normalize: norm }),
      });
      const data = await res.json();
      const s = {
        original: data.original_query,
        normalized_query: data.query_used,
        normalization_steps: (data.normalization && data.normalization.steps) || [],
        parsed: data.parsed,
        match: data.match,
        behavior: data.behavior,
      };
      document.getElementById('summary').textContent = JSON.stringify(s, null, 2);
      document.getElementById('full').textContent = JSON.stringify(data, null, 2);
    }
    document.getElementById('run').onclick = run;
  </script>
</body>
</html>
"""


def run_once(query: str, *, normalize: bool) -> dict:
    return process_query(query, apply_normalization=normalize).to_dict()


def serve(host: str, port: int) -> None:
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args) -> None:  # noqa: A003
            sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

        def do_GET(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            if path in {"/", "/index.html"}:
                body = HTML_PAGE.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            self.send_error(404)

        def do_POST(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            if path != "/api/query":
                self.send_error(404)
                return
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length)
            try:
                payload = json.loads(raw.decode("utf-8") or "{}")
            except json.JSONDecodeError:
                self.send_error(400, "invalid JSON")
                return
            query = str(payload.get("query") or "")
            normalize = bool(payload.get("normalize", True))
            result = run_once(query, normalize=normalize)
            body = json.dumps(result).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    httpd = ThreadingHTTPServer((host, port), Handler)
    print(f"Shopper-query harness at http://{host}:{port}/")
    httpd.serve_forever()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd")

    p_query = sub.add_parser("query", help="Run one query on the CLI")
    p_query.add_argument("text", nargs="?", default="")
    p_query.add_argument("--normalize", action="store_true")
    p_query.add_argument("--no-normalize", action="store_true")
    p_query.add_argument("--json", action="store_true")

    p_serve = sub.add_parser("serve", help="Local developer page")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8771)

    p_eval = sub.add_parser("eval-baseline", help="Run baseline evaluator")
    p_eval.add_argument("--cases", type=Path, default=None)
    p_eval.add_argument("--output-dir", type=Path, default=None)

    p_cmp = sub.add_parser("eval-compare", help="Run comparison evaluator")
    p_cmp.add_argument("--cases", type=Path, default=None)
    p_cmp.add_argument("--output-dir", type=Path, default=None)

    args = parser.parse_args(argv)
    if args.cmd is None:
        parser.print_help()
        return 2

    if args.cmd == "query":
        text = args.text
        if not text:
            text = sys.stdin.read().strip()
        normalize = True
        if args.no_normalize:
            normalize = False
        elif args.normalize:
            normalize = True
        else:
            normalize = False  # CLI default: raw path unless --normalize
        if args.normalize:
            normalize = True
        result = run_once(text, normalize=normalize)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"original:    {result['original_query']}")
            print(f"query_used:  {result['query_used']}")
            if result.get("normalization"):
                print(f"norm steps:  {len(result['normalization']['steps'])}")
            print(f"product:     {result['parsed']['product_text']}")
            print(f"price:       {result['parsed']['price']}")
            print(f"promo:       {result['parsed']['promotion_type']}")
            print(f"qty:         {result['parsed']['required_quantity']}")
            print(f"size:        {result['parsed']['package_size_text']}")
            print(f"match:       {result['match']['status']} → {result['match']['matched_family_id']}")
            print(
                f"behavior:    {result['behavior']['behavior']} "
                f"(safe={result['behavior']['automatic_continuation_safe']})"
            )
        return 0

    if args.cmd == "serve":
        serve(args.host, args.port)
        return 0

    if args.cmd == "eval-baseline":
        from shopper_query.eval_baseline import main as baseline_main

        argv2: list[str] = []
        if args.cases:
            argv2 += ["--cases", str(args.cases)]
        if args.output_dir:
            argv2 += ["--output-dir", str(args.output_dir)]
        return baseline_main(argv2)

    if args.cmd == "eval-compare":
        from shopper_query.eval_compare import main as compare_main

        argv2 = []
        if args.cases:
            argv2 += ["--cases", str(args.cases)]
        if args.output_dir:
            argv2 += ["--output-dir", str(args.output_dir)]
        return compare_main(argv2)

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
