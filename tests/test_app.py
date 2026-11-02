import os, tempfile
import app as module

def test_endpoints():
    with tempfile.TemporaryDirectory() as d:
        module.DB=os.path.join(d,"test.db")
        module.init_db()
        client=module.app.test_client()
        assert client.get("/api/summary").json["totals"]["orders"]==0
        with open(os.path.join(os.path.dirname(__file__),"..","data","sample_sales.csv"),"rb") as f:
            r=client.post("/api/upload",data={"file":(f,"sales.csv")},content_type="multipart/form-data")
        assert r.status_code==200
        assert r.json["imported"]>0
        assert client.get("/api/summary").json["totals"]["revenue"]>0
        assert client.get("/api/forecast").status_code==200
        assert client.get("/api/export").status_code==200
