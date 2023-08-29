ARG FRAPPE_VERSION=14
# Prepare builder image
FROM frappe/bench:latest as assets

ARG FRAPPE_VERSION=14
ARG ERPNEXT_VERSION=14
ARG APP_NAME

# Setup frappe-bench using FRAPPE_VERSION
RUN bench init  --skip-redis-config-generation --verbose --skip-assets --frappe-branch v14.24.0 /home/frappe/frappe-bench

WORKDIR /home/frappe/frappe-bench



# Comment following if ERPNext is not required
#RUN bench get-app version-14 --skip-assets
# Copy custom app(s)

RUN mv ./apps/frappe/.git ./apps/.git

RUN rm -rf /home/frappe/frappe-bench/apps/frappe
RUN rm -rf /home/frappe/frappe-bench/apps/erpnext

# RUN ls apps/


COPY --chown=frappe:frappe ./frappe /home/frappe/frappe-bench/apps/frappe
COPY --chown=frappe:frappe ./erpnext /home/frappe/frappe-bench/apps/erpnext

RUN rm -rf /home/frappe/frappe-bench/apps/erpnext/.git
# COPY --chown=frappe:frappe ./frappe/frappe /home/frappe/frappe-bench/local
RUN cp -R ./apps/.git ./apps/frappe/.git
RUN cp -R ./apps/.git ./apps/erpnext/.git

# RUN mv ./apps/.git ./apps/erpnext/.git

# RUN echo $(ls -1 /home/frappe/frappe-bench/apps)
# COPY --chown=frappe:frappe ./apps/proj apps/proj

# Setup dependencies
RUN bench setup requirements

# Build static assets, copy files instead of symlink
RUN bench build --verbose --hard-link --production --apps frappe,erpnext

RUN touch /home/frappe/frappe-bench/sites/assets/cc

# Use frappe-nginx image with nginx template and env vars
FROM frappe/frappe-nginx:v14

# Remove existing assets
USER root


RUN rm -rf /usr/share/nginx/html/assets

# Copy built assets
COPY --from=assets /home/frappe/frappe-bench/sites/assets /usr/share/nginx/html/assets
COPY --from=assets /home/frappe/frappe-bench/sites/assets /usr/share/nginx/html/nextasset


# Use non-root user
USER 1000
