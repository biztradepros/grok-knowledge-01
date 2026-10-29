import sys, json, time, hashlib, re
from docling.document_converter import DocumentConverter
src, out = sys.argv[1], sys.argv[2]
t=time.time()
res = DocumentConverter().convert(src)
doc = res.document
dt=time.time()-t
tables = doc.tables
print("status", res.status, "secs", round(dt,1), "tables", len(tables), "texts", len(doc.texts))
hit=None
for i,tb in enumerate(tables):
    df = tb.export_to_dataframe(doc=doc)
    s = df.to_csv(index=False)
    if '단일판매' in s or '계약금액총액' in s or '선화' in s:
        hit=(i,df); break
if hit:
    i,df=hit
    print("table_index", i, "shape", df.shape); print(df.head(12).to_string()[:3000])
    df.to_csv(out+"_table.csv", index=False)
    rows=[r for r in df.astype(str).values.tolist() if any('대전' in c for c in r)]
    json.dump({"source_sha256":hashlib.sha256(open(src,'rb').read()).hexdigest(),"table_index":i,"daejeon_rows":rows},open(out+"_daejeon.json","w"),ensure_ascii=False,indent=1)
    print("daejeon rows:"); [print(r) for r in rows]
open(out+".md","w").write(doc.export_to_markdown())
