FROM ghcr.io/openfaas/of-watchdog:0.9.6 as watchdog
FROM python:3.11-slim

# Install watchdog
COPY --from=watchdog /fwatchdog /usr/bin/fwatchdog
RUN chmod +x /usr/bin/fwatchdog

# Create app directory
RUN addgroup --system pass-gen && adduser --system --ingroup pass-gen pass-gen
WORKDIR /home/pass-gen

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy function code
COPY handler.py .

# Set permissions
RUN chown -R pass-gen:pass-gen /home/pass-gen
USER pass-gen

# Configure the watchdog
ENV fprocess="python handler.py"
ENV mode="http"
ENV upstream_url="http://127.0.0.1:8080"
ENV DATABASE_URL="postgresql://cofrap:cofrap123@localhost/cofrap"

EXPOSE 8080

HEALTHCHECK --interval=3s CMD [ -e /tmp/.lock ] || exit 1

CMD ["fwatchdog"]