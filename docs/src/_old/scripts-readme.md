Running the smoke test
======================

Once you have deployed the MVP on Kubernetes (see _README.), you can run the smoke test by running:
```
bash scripts/smoketest.sh
```

This will run the smoke test script.

Note: the smoke test is very simple, and just counts the number of containers in the Running state. Therefore, if your deployment deploys a different number of containers, the smoke test will fail, and you'll need to update the underlying bash script so that the number of containers is correct. 
