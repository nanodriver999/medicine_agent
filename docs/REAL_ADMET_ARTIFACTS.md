# Real ADMET run evidence packaging

The manual real-model job retains its installed dependencies, Python environment, source molecular pool, pool SHA256, model output and evidence JSON together under workspace-backed artifact paths. Upload-on-failure helps diagnose missing weights or insufficient resources. Evidence remains a short-lived GitHub Actions artifact; it is not proof of model accuracy or a reproducible fixed model-weight revision. No real model inference is run during ordinary CI.
