# api-channel demo

Steps to run the demo (run in 2 terminals):

1. Setup the basics

		docker network create igl_local_devnet

2. Launch SG endpoint (receiving side)::

		export COMPOSE_PROJECT_NAME=au_sg_api_channel_sg_endpoint
		python pie.py api.start
		python pie.py test.start
		python pie.py test.subscribe
		python pie.py api.logs

3. Launch AU endpoint (sending side)::

		export COMPOSE_PROJECT_NAME=au_sg_api_channel_au_endpoint
		python pie.py api.start
		python pie.py test.send_message

4. Inspect SG logs to see if there is a received message and callback notification.

5. To stop all containers run in both terminals::

		python pie.py api.stop
