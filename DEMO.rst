# api-channel demo

Steps to run the demo (run in 2 terminals):

1. Launch SG endpoint (receiving side)::

		export COMPOSE_PROJECT_NAME=au_sg_channel_sg_endpoint
		python pie.py api.start
		python pie.py test.start
		python pie.py test.subscribe
		python pie.py api.logs

2. Launch AU endpoint (sending side)::

		export COMPOSE_PROJECT_NAME=au_sg_channel_au_endpoint
		python pie.py api.start
		python pie.py test.send_message

3. Inspect SG logs to see if there is a received message and callback notification.

4. To stop all containers run in both terminals::

		python pie.py api.stop
