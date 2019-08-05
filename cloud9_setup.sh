#! /usr/bin/env bash

### Git setup ###
if [ -z "$(git config --get user.name)" ]
then
  echo "Enter name for git commits, may contain spaces: (Press enter to skip)."
  read name
  if [ ! -z "${name}" ]
  then
    git config --global user.name "${name}"
  else
    echo -e "Skipping...\n"
  fi
fi

if [ -z "$(git config --get user.email)" ]
then
  echo "Enter email for git commits: (Press enter to skip)."
  read email
  if [ ! -z "${email}" ]
  then
    git config --global user.email "${email}"
  else
    # Do not accept commits without user/email
    git config --global user.useconfigonly true
    echo -e "Skipping...\n"
  fi
fi


echo "Set git aliases co, ci, st, and br to call checkout, commit, status, and branch? (y/n)"
read set_aliases
if [ ! -z "${set_aliases}" ] && [ "${set_aliases}" == "y" ]
then
  git config --global alias.br branch
  git config --global alias.st status
  git config --global alias.ci commit
  git config --global alias.co checkout
else
  echo -e "Skipping...\n"
fi




### Key setup ###
if [ ! -e ~/.ssh/id_rsa.pub ]
then
  fn_key=~/.ssh/id_rsa
  echo "Generating key-pair. Add comment for easy identification of public key"
  echo "(could include your name, cloud9 instance name, and aws account)."
  read comment
  if [ -z "${comment}" ]
  then
  	ssh-keygen -q -f $fn_key 
  else
  	ssh-keygen -q -f $fn_key -C "$comment"
  fi
fi


# Install cloud9 CLI
if [ -z "$(command -v c9)" ]
then
  echo "installing c9..."
  npm install -g c9 > /dev/null
fi


### Suggestions for setting up dev env ###
echo -e "\n# Useful commands and suggestions for setting up a development environment on Cloud9"

echo -e "\n# Public key:"
cat ~/.ssh/id_rsa.pub

echo -e "\n# Add your public key to github: https://github.com/settings/keys"

echo -e "\n# Clone data-lake-config"
echo "git clone git@github.com:SanofiDSE/data-lake-config.git"

echo -e "\n# For tab completion with git add this line to ~/.bash_profile:"
echo "source /etc/bash_completion.d/git"

echo -e "\n# Requirement for pytest-spark: install java 1.8 and set the environment variable JAVA_HOME"
echo "sudo yum install java-1.8.0"
echo "# Add the line: 'export JAVA_HOME=/usr/lib/jvm/jre-1.8.0' to ~/.bash_profile"

echo -e "\n# The alias python='python27' can cause problems with virtualenv and python2.\n# This alias is set in the file ~/.bashrc"
