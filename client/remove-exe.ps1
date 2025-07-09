if(!(Test-Path ./app)){
    mkdir ./app
}else{
    rm ./app/*
}

rm ./app/client.exe -ErrorAction SilentlyContinue

if (Test-Path ./dist/client.exe) {
    mv ./dist/client.exe ./app/client.exe
    echo "Moved new executable to app folder"
} else {
    echo "No executable found"
}

try {
    rm -r dist -ErrorAction SilentlyContinue
    rm -r build -ErrorAction SilentlyContinue
    rm client.spec -ErrorAction SilentlyContinue
}
catch {
    echo "No build files to remove"
}

