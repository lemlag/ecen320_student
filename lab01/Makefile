about:
	cat aboutme.txt

reverse:
	rev aboutme.txt > reverse.txt

upper:
	cat aboutme.txt | sed 's/[a-z]/\U&/g' > upper.txt

lineno:
	nl aboutme.txt > lineno.txt

bottom:
	tail -n 3 aboutme.txt > bottom.txt

clean:
	rm -f bottom.txt reverse.txt lineno.txt upper.txt
