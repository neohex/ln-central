from django.shortcuts import render
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions

from .models import LightningNode
from .models import LightningInvoice
from .serializers import LightningNodeSerializer
from .serializers import LightningInvoiceSerializer

import time
import datetime
import json
import subprocess


class RunCommandException(Exception):
	pass
		

def log(msg):
	timestamp = datetime.datetime.now()
	timestamp = timestamp.strftime("%Y-%m-%d %H:%M:%S")
	msg = "{} {}".format(timestamp, msg)
	print(msg)


def run(cmd, timeout=5, try_num=3, run_try_sleep=1):
	log("Running command: {}".format(cmd))
	accumulated_timeout = 0
	for _ in range(try_num):
		try_start = time.time()
		try:
			raw = subprocess.check_output(
			       cmd,
			       timeout=timeout
			    ).decode("utf-8")
			break
		except Exception as e:
		    print(e)
		    print("Sleeping for {} seconds".format(run_try_sleep))
		    time.sleep(run_try_sleep)

		try_duration = time.time() - try_start
		accumulated_timeout += try_duration

		if accumulated_timeout > timeout:
		    raise RunCommandException("Run command {} timeout after {} seconds".format(cmd, accumulated_timeout))

	else:
		raise RunCommandException("Failed command: {}".format(cmd))

	return json.loads(raw)


class LightningNodeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows lightning nodes to be viewed
    """
    queryset = LightningNode.objects.all()
    serializer_class = LightningNodeSerializer


class LightningInvoiceList(APIView):
    """
    List all snippets, or create a new snippet.
    """

    LNCLI_BIN = "~lightning/gocode/bin/lncli"

    def addinvoice(self, memo):
    	cmd = [
    		LightningInvoicetList.LNCLI_BIN,
    		"--macaroonpath", "/etc/biostar/invoice.macaroon",
    		"--tlscertpath", "/etc/biostar/tls.cert",
    		"--rpcserver", "ec2-34-217-175-162.us-west-2.compute.amazonaws.com:10009",
    		"addinvoice", "--memo", memo, "--amt", "300"
    	]
    	return run(cmd)

    def get(self, request, format=None):

        # # Example:
        # invoice = [
        #     {
        #         "r_hash": "48452417b7d351bdf1ce493521ffbc07157c68fd9340ba2aeead0c29899fa4b4",
        #         "pay_req": "lnbc3u1pwfapdepp5fpzjg9ah6dgmmuwwfy6jrlauqu2hc68ajdqt52hw45xznzvl5j6qdqydp5scqzysdhdt9dngs8vw5532tcwnjvazn75cevfzz5r4drla8uvqlkt5u63nu5lrsa4s2q4rwmfe93yt7gavhrv3aq8rx3u842spdkwzhzketgsqv9zemq",
        #         "add_index": 11
        #      }
        # ]
        invoice = [json.loads(self.addinvoice(request.GET["memo"]))]  # deserialize      
        serializer = LightningInvoiceSerializer(invoice, many=True)  # re-serialize

        return Response(serializer.data)