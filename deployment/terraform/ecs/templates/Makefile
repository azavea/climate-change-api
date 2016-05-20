all: management.json web.json

.PHONY: all clean

management.json: management.yaml
	../../yml2json.py management.yaml

web.json: web.yaml
	../../yml2json.py web.yaml

clean:
	-rm -rf management.json web.json
