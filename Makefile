all:

clean:
	-rm *~
	$(MAKE) -C homicidehotel clean
push:
	git push
