HELM_RELEASE=test
KUBE_NAMESPACE=integration
path="{range .items[*]}"
path="   $path{.metadata.name}{'\n'}"
path="   $path{range .spec.containers[*]}"
path="        $path{.name}{'\t'}{.image}{'\n\n'}"
path="   $path{end}{'\n'}"
path="$path{end}{'\n'}"
kubectl get pods -l release=$HELM_RELEASE -n $KUBE_NAMESPACE -o jsonpath="$path"
