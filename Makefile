NAME = taskmaster

all: $(NAME)

$(NAME):
	@python3 main.py

clean:
	@echo "Cleaning repository ..."
	@rm -rf *.pyc
	@rm -rf *.swp
	@rm -rf __pycache__

re: clean all
