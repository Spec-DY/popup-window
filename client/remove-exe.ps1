if(!(Test-Path ./app)){
    mkdir ./app
}else{
    Remove-Item ./app/*
}

Remove-Item ./app/client.exe -ErrorAction SilentlyContinue

if (Test-Path ./dist/client.exe) {
    Move-Item ./dist/client.exe ./app/client.exe
    Write-Output "Moved new executable to app folder"
} else {
    Write-Output "No executable found"
}

try {
    Remove-Item -r dist -ErrorAction SilentlyContinue
    Remove-Item -r build -ErrorAction SilentlyContinue
    Remove-Item client.spec -ErrorAction SilentlyContinue
}
catch {
    Write-Output "No build files to remove"
}

