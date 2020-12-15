#!/bin/bash
set -e
set -o pipefail

# create a Namespace admin account

# Add user to k8s using service account, no RBAC (must create RBAC after this script)
if [[ -z "$1" ]]; then
 echo "usage: $0 <service_account_name> <Namespace>"
 exit 1
fi
if [[ -z "$2" ]]; then
 echo "usage: $0 <service_account_name> <Namespace>"
 exit 1
fi

SERVICE_ACCOUNT_NAME=$1
NAMESPACE="$2"
KUBECFG_FILE_NAME="/tmp/kube/k8s-${SERVICE_ACCOUNT_NAME}-${NAMESPACE}-conf"
TARGET_FOLDER="/tmp/kube"
KUBECFG_URL=""

kubectl -n ${NAMESPACE} delete rolebinding/${SERVICE_ACCOUNT_NAME}-ns-admin || true
kubectl -n ${NAMESPACE} delete role/${SERVICE_ACCOUNT_NAME}-ns-admin || true
kubectl -n ${NAMESPACE} delete secret/${SERVICE_ACCOUNT_NAME}-secret || true
kubectl -n ${NAMESPACE} delete serviceaccount/${SERVICE_ACCOUNT_NAME} || true

create_target_folder() {
    echo -n "Creating target directory to hold files in ${TARGET_FOLDER}..."
    mkdir -p "${TARGET_FOLDER}"
    printf "done"
}

create_service_account() {
    echo -e "\\nCreating a service account in ${NAMESPACE} namespace: ${SERVICE_ACCOUNT_NAME}"
    kubectl create sa "${SERVICE_ACCOUNT_NAME}" --namespace "${NAMESPACE}"

    kubectl --namespace "${NAMESPACE}" apply -f - <<EOF
---
kind: RoleBinding
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: ${SERVICE_ACCOUNT_NAME}-ns-admin
subjects:
- kind: ServiceAccount
  name: ${SERVICE_ACCOUNT_NAME}
  namespace: ${NAMESPACE}
roleRef:
  kind: Role
  name: ${SERVICE_ACCOUNT_NAME}-ns-admin
  apiGroup: rbac.authorization.k8s.io
---

kind: Role
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: ${SERVICE_ACCOUNT_NAME}-ns-admin
rules:
- apiGroups: [""]
  resources: ["namespaces", "storageclasses", "serviceaccounts",
              "resourcequotas", "persistentvolumes", "limitranges",
              "nodes", "componentstatuses"]
  verbs: ["list", "get", "watch"]
- apiGroups: ["autoscaling"]
  resources: ["horizontalpodautoscalers"]
  verbs: ["list", "get", "watch"]
- apiGroups: ["discovery.k8s.io"]
  resources: ["endpointslices"]
  verbs: ["list", "get", "watch"]
- apiGroups: ["admissionregistration.k8s.io"]
  resources: ["mutatingwebhookconfigurations", "validatingwebhookconfigurations"]
  verbs: ["list", "get", "watch"]
- apiGroups: ["apiextensions.k8s.io"]
  resources: ["customresourcedefinitions"]
  verbs: ["list", "get", "watch"]
- apiGroups: ["apiregistration.k8s.io"]
  resources: ["apiservices"]
  verbs: ["list", "get", "watch"]
- apiGroups: ["apps"]
  resources: ["controllerrevisions"]
  verbs: ["list", "get", "watch"]
- apiGroups: ["node.k8s.io"]
  resources: ["runtimeclasses"]
  verbs: ["list", "get", "watch"]
- apiGroups: ["policy"]
  resources: ["poddisruptionbudgets", "podsecuritypolicies"]
  verbs: ["list", "get", "watch"]
- apiGroups: ["rbac.authorization.k8s.io"]
  resources: ["rolebindings", "roles"]
  verbs: ["list", "get", "watch"]
- apiGroups: ["storage.k8s.io"]
  resources: ["storageclasses", "volumeattachments"]
  verbs: ["list", "get", "watch"]
- apiGroups: ["", "batch", "apps"]
  resources: ["deployments", "jobs", "pods", "configmaps",
              "persistentvolumeclaims", "services", "secrets",
              "endpoints", "events", "podtemplates", "replicationcontrollers",
              "daemonsets", "replicasets", "statefulsets", "cronjobs"]
  verbs: ["list", "get", "watch", "create", "update", "patch", "delete"]
- apiGroups: ["etcd.database.coreos.com"]
  resources: ["etcdbackups", "etcdclusters", "etcdrestores"]
  verbs: ["list", "get", "watch", "create", "update", "patch", "delete"]
- apiGroups: ["events.k8s.io"]
  resources: ["events"]
  verbs: ["list", "get", "watch", "create", "update", "patch", "delete"]
- apiGroups: ["extensions"]
  resources: ["ingresses"]
  verbs: ["list", "get", "watch", "create", "update", "patch", "delete"]
- apiGroups: ["networking.k8s.io"]
  resources: ["ingressclasses", "ingresses", "networkpolicies"]
  verbs: ["list", "get", "watch", "create", "update", "patch", "delete"]

EOF

}

get_secret_name_from_service_account() {
    echo -e "\\nGetting secret of service account ${SERVICE_ACCOUNT_NAME} on ${NAMESPACE}"
    SECRET_NAME=$(kubectl get sa "${SERVICE_ACCOUNT_NAME}" --namespace="${NAMESPACE}" -o json | jq -r .secrets[].name)
    echo "Secret name: ${SECRET_NAME}"
}

extract_ca_crt_from_secret() {
    echo -e -n "\\nExtracting ca.crt from secret..."
    kubectl get secret --namespace "${NAMESPACE}" "${SECRET_NAME}" -o json | jq \
    -r '.data["ca.crt"]' | base64 -d > "${TARGET_FOLDER}/ca.crt"
    printf "done"
}

get_user_token_from_secret() {
    echo -e -n "\\nGetting user token from secret..."
    USER_TOKEN=$(kubectl get secret --namespace "${NAMESPACE}" "${SECRET_NAME}" -o json | jq -r '.data["token"]' | base64 -d)
    printf "done"
}

set_kube_config_values() {
    context=$(kubectl config current-context)
    echo -e "\\nSetting current context to: $context"

    CLUSTER_NAME=$(kubectl config get-contexts "$context" | awk '{print $3}' | tail -n 1)
    echo "Cluster name: ${CLUSTER_NAME}"

    ENDPOINT=$(kubectl config view \
    -o jsonpath="{.clusters[?(@.name == \"${CLUSTER_NAME}\")].cluster.server}")
    echo "Endpoint: ${ENDPOINT}"

    # Set up the config
    echo -e "\\nPreparing k8s-${SERVICE_ACCOUNT_NAME}-${NAMESPACE}-conf"
    echo -n "Setting a cluster entry in kubeconfig..."
    KUBECONFIG=${KUBECFG_FILE_NAME} kubectl config set-cluster "${CLUSTER_NAME}" \
    --kubeconfig="${KUBECFG_FILE_NAME}" \
    --server="${ENDPOINT}" \
    --certificate-authority="${TARGET_FOLDER}/ca.crt" \
    --embed-certs=true

    echo -n "Setting token credentials entry in kubeconfig..."
    KUBECONFIG=${KUBECFG_FILE_NAME} kubectl config set-credentials \
    "${SERVICE_ACCOUNT_NAME}-${NAMESPACE}-${CLUSTER_NAME}" \
    --kubeconfig="${KUBECFG_FILE_NAME}" \
    --token="${USER_TOKEN}"

    echo -n "Setting a context entry in kubeconfig..."
    KUBECONFIG=${KUBECFG_FILE_NAME} kubectl config set-context \
    "${SERVICE_ACCOUNT_NAME}-${NAMESPACE}-${CLUSTER_NAME}" \
    --kubeconfig="${KUBECFG_FILE_NAME}" \
    --cluster="${CLUSTER_NAME}" \
    --user="${SERVICE_ACCOUNT_NAME}-${NAMESPACE}-${CLUSTER_NAME}" \
    --namespace="${NAMESPACE}"

    echo -n "Setting the current-context in the kubeconfig file..."
    KUBECONFIG=${KUBECFG_FILE_NAME} kubectl config use-context "${SERVICE_ACCOUNT_NAME}-${NAMESPACE}-${CLUSTER_NAME}" \
    --kubeconfig="${KUBECFG_FILE_NAME}"
}

#Deletes pre-existing namespaces
delete_older_namespaces(){
    echo -e -n "\\nDeleting the pre-existing namespaces..."
    kubectl get namespaces
    kubectl delete namespaces ${NAMESPACE}
}

# Push kubeconfig file to the Nexus Repo
push_kubeconfig_to_nexus() {
  echo "######### UPLOADING ${KUBECFG_FILE_NAME}";
  # TODO: Make file path with KUBE_NAMESPACE
  curl -v -u $RAW_USER:$RAW_PASS --upload-file ${KUBECFG_FILE_NAME} ${RAW_HOST}/repository/k8s-ci-creds/${KUBECFG_FILE_NAME};
  echo "######### UPLOADED ${KUBECFG_FILE_NAME}";
  # TODO: Get File URL into a variable.
  KUBECFG_URL="${RAW_HOST}/repository/k8s-ci-creds/..."
}

create_target_folder
create_service_account
get_secret_name_from_service_account
extract_ca_crt_from_secret
get_user_token_from_secret
set_kube_config_values
push_kubeconfig_to_nexus
delete_older_namespaces

# echo -e "\\nAll done! Test with:"
# echo "KUBECONFIG=${KUBECFG_FILE_NAME} kubectl get pods"
# echo "you should not have any permissions by default - you have just created the authentication part"
# echo "You will need to create RBAC permissions"
# echo "get Pods:"
# KUBECONFIG=${KUBECFG_FILE_NAME} kubectl get pods
# echo ""
# echo "Show KUBECONFIG:"
# KUBECONFIG=${KUBECFG_FILE_NAME} kubectl config view --flatten --raw
# echo "In KUBECONFIG=${KUBECFG_FILE_NAME}"

echo -e "\\n All done!"
echo "You can get the kubeconfig file from the url: ${KUBECFG_URL} with:"
echo "curl ${KUBECFG_URL}"
echo "You have the following permissions:"
# TODO: List permissions
echo "Example usage:"
echo "kubectl --kubeconfig=KUBECFG_FILE get pods"
# TODO: This documentation will be expanded on ST-559 with more examples for developer use cases/workflows
