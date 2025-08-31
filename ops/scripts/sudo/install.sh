#!/bin/sh

SRC_DIR='/opt/home-server/ops/scripts/sudo'

install -D -o root -g root -m 0755 "$SRC_DIR/apt-update.sh" /usr/local/bin/home-server-apt-update
install -D -o root -g root -m 0755 "$SRC_DIR/apt-upgrade.sh" /usr/local/bin/home-server-apt-upgrade
