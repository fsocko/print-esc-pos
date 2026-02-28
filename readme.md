# 80mm ESC/POS printer

## PROBLEMS:
	
## DOCS:
	GH-Pages: https://fsocko.github.io/print-esc-pos/
	https://python-escpos.readthedocs.io/en/latest/user/methods.html#escpos-class


## TODO:
	### Horizontal image print - do a rot like in render font image
	
	### On HTTP server, Still have a CORS issue with fonts (and images?).
	### basic markdown formatter in text mode.

	### When sending formatted text from mobile, it looks like canvas.js breaks and does not render text.	

# Server:

## Server Start:
	
	uvicorn server.server_fastapi:app --host 0.0.0.0 --reload --port 8069

## Token: 
	Requires cmd env variable:  
		export THERMAL_API_TOKEN=''

## endpoints:

print API: 			http://localhost:8069/api/print
docs:			 			http://localhost:8069/docs
web-formatter: 	http://localhost:8069/formatter
