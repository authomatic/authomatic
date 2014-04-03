.. tip::
	
	Some of the providers don't support authorization from apps running on **localhost**.
	Probably the best solution is to use an arbitrary domain as an alias of the ``127.0.0.1`` IP address.

	You can do this on UNIX systems by adding an alias to the ``/etc/hosts`` file.

	.. code-block:: none
	    :emphasize-lines: 3

		# /etc/hosts
		127.0.0.1    localhost
		127.0.0.1    yourlocalhostalias.com

	You can do this on Windows systems by adding an alias in the ``C:\Windows\system32\drivers\etc\hosts`` file.
	
	.. code-block:: none
	    :emphasize-lines: 1

		127.0.0.1     yourlocalhostalias.com
