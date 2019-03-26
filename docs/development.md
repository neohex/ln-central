# Install

Requierments:

  * `python2.7`
  * `pip2.7`
  * `python3`
  * `pip3`
  * `virtualenv`

Get sourcecode, setup virtualenv local directories, and install requierments::

	git clone https://github.com/alevchuk/biostar-central-ln.git
	cd biostar-central-ln
	./bistar.sh install

## Start writer

	# Initialize local db	
	./biostar.sh writer-dev migrate

	# Create admin user
	./biostar.sh writer-dev createsuperuser --email admin@example.com --username admin

	# Start writer (backend)
	./biostar.sh writer-dev runserver

Visit http://localhost:8000 to explore the backend API

## Start reader

	# Initialize local db 
	./biostar.sh init
	
	# Run webserver
	AVATAR_SERVER_NAME=https://ln.support ./biostar.sh run


Visit http://localhost:8080 to see the site
