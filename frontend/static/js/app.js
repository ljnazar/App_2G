/* Previene la acción por defecto del formulario (enviar contenido como parametro de url) */
let form = document.querySelector(".form")
form.addEventListener("submit", function(event){
    event.preventDefault();
});

let input = document.querySelector(".input");
let msj_datos = document.getElementById("mensaje");
let table = document.getElementById("table");
let boton = document.getElementById("boton-buscar");
let loader = document.getElementById("loader");
let msj_error = document.getElementById("error");
let msj_sran = document.getElementById("sran");
let container_checkbox = document.getElementById("container_checkbox");
let display_timer = document.getElementById("timer");
let container_timer = document.getElementById("container_timer");
let linea_default = document.getElementById("linea_default");

let countDown = '';
let intervalRequest = '';
let flag_update_values = false;


loader.style.display = "none";

/* Agrega un evento que cambia el valor del value en el html */
let checkbox = document.getElementById('checkbox');
checkbox.addEventListener('change', function(event){
    if(checkbox.checked){
        checkbox.value = 'on';
        console.log(`switch: ${checkbox.value}`);
    }
    else{
        checkbox.value = 'off';
        console.log(`switch: ${checkbox.value}`);
    }
});

let btnDetener = document.getElementById("boton-detener")
btnDetener.addEventListener("click", function(event){
    endRealTime();
});

/* Valida que el string ingresado sea AlfaNumerico */
function NumText(string){
    var out = '';
    // Se añaden los caracteres validos
    var filtro = 'abcdefghijklmnñopqrstuvwxyzABCDEFGHIJKLMNÑOPQRSTUVWXYZ1234567890';
    
    for (var i=0; i<string.length; i++){
        if (filtro.indexOf(string.charAt(i)) != -1){
            out += string.charAt(i);
        }
    }
    if(string === out){
        return true;
    }
    else{
        return false;
    }
}

function update_values() {

    flag_update_values = true;

    console.log(display_timer.innerHTML);

    axios.get(`http://localhost:5000/api/${cellid}/_update`)
    .then(function (response) {

        console.log(response.data);

        let matriz_BCF = response.data[cellid].matriz_BCF;
        let flag_SRAN = response.data[cellid].flag_SRAN;
        let matriz_ET = response.data[cellid].matriz_ET;
        let alarmas_ET = response.data[cellid].alarmas_ET;

        table.innerHTML = render_tabla(flag_SRAN, matriz_BCF, matriz_ET, alarmas_ET);

        console.log('Se actualizaron los valores');

    })
    .catch(function (error) {
        console.log('Error');
        msj_error.innerHTML = `<div class="alert alert-warning max-ancho">
                                  <strong>Error: No se pudo realizar la consulta en tiempo real</strong>
                               </div>`;
    });
}

/* Se detacta cuando se cierra la pestaña del navegador o se actualiza */
window.addEventListener("beforeunload", function (e) {
    // Hacemos que si se están actualizando los valores en tiempo real se cierre la sesion telnet
    if(e.isTrusted && flag_update_values){
        axios.get(`http://localhost:5000/_CloseTn`)
    }
});

function render_tabla(flag_SRAN, matriz_BCF, matriz_ET, alarmas_ET){

    tabla = `<table id="ancho-tabla" class="table table-bordered max-ancho">
                <thead class="thead-dark">
                    <tr>
                        <th scope="col">BCF/ET</th>
                        <th scope="col">Estado</th>
                        <th scope="col">Alarma</th>
                        <th scope="col"></th>
                    </tr>
                </thead>` + 
                matriz_BCF.map(function(array_BCF) {

                    let ET = '';
                    let ET_ant = '';
                    let estado_ET = '';
                    let estado_ET_alarm = '';
                    let alarm_ET = '';

                    BCF =   `<thead class="thead-light">
                                <tr>
                                    <th scope="col">BCF: ${array_BCF[0]}</th>
                                    <th scope="col">${array_BCF[1]}</th>
                                    <th scope="col"></th>`;
                                if(array_BCF[1] == 'WO'){
                                    estado_BCF = `<th scope="col"><i class="fas fa-check fa-lg"></i></th>
                                </tr>
                            </thead>`;
                                }
                                else{
                                    estado_BCF = `<td class="text-center"><i class="fas fa-times fa-lg"></i></td>
                                </tr>
                            </thead>`;
                                }

                                + `<tbody>` +

                                array_BCF.map(function(elemento, index) {
                                    if (flag_SRAN == false){
                                        // Si es igual o mayor a dos lavariable "elemento" es la ET
                                        if(index >= 2){
                                            ET = `<tr>
                                                    <th scope="row">ET - ${elemento}</th>`;

                                            matriz_ET.map(function(array_ET) {
                                                if(array_ET[0] == elemento){
                                                    estado_ET = ` <td class="text-center">${array_ET[1]}</td>
                                                                  <td class="text-center">${array_ET[2]}</td>`;
                                                                        
                                                    if(array_ET[1] == 'WO-EX' && array_ET[2] == 'NO'){
                                                        estado_ET_alarm = `<th scope="col"><i class="fas fa-check fa-lg"></i></th>
                                                                        </tr>`;
                                                    }
                                                    else{
                                                        estado_ET_alarm = `<td class="text-center"><i class="fas fa-times fa-lg"></i></td>
                                                                        </tr>`;
                                                    }

                                                    alarmas_ET.map(function(array_alarm) {
                                                        if(array_ET[0] == array_alarm[0]){
                                                            alarm_ET = `<th scope="row" id="alarm" colspan="4"><strong>${array_alarm[1]}</strong></th>`;
                                                        }
                                                    });

                                                    ET = ET + estado_ET + estado_ET_alarm + alarm_ET;
                                                }
                                            });

                                            if (ET_ant != ET){
                                                ET = ET_ant + ET;
                                            }
                                            estado_ET = '';
                                            estado_ET_alarm = '';
                                            alarm_ET = '';
                                            ET_ant = ET;                      
                                        }
                                    }
                                });

                    return BCF+estado_BCF+ET;
                // La funcion map() devuelve un array y para eliminar la coma que aparece en chrome se usa join('')
                }).join(''); +
                                            
                `</tbody>
            </table>`;

    return tabla;
}

function startTimer(duration, intervalRequest) {
    let timer = duration, minutes, seconds;
    // Se setea la veriable global countDown
    countDown = setInterval(() => {
        minutes = parseInt(timer / 60, 10);
        seconds = parseInt(timer % 60, 10);

        minutes = minutes < 10 ? "0" + minutes : minutes;
        seconds = seconds < 10 ? "0" + seconds : seconds;

        display_timer.textContent = minutes + ":" + seconds;

        if (--timer < 0) {
            timer = duration;
        }
        if (display_timer.innerHTML == '00:00') {
            endRealTime();
        }
    }, 1000);
}

function endRealTime() {
    clearInterval(countDown);
    clearInterval(intervalRequest);
    container_timer.style.display = "none";
    input.style.display = "block";
    boton.style.display = "block";
    linea_default.style.display = "block";
    checkbox.checked = false;
    checkbox.value = 'off';
    console.log(`switch: ${checkbox.value}`);
    container_checkbox.style.display = "block";
    display_timer.innerHTML = '03:00';

    axios.get(`http://localhost:5000/_CloseTn`)
    .then(function (response) {
        console.log(response.data);
    })
    .catch(function (error) {
        console.log('Error');
    });    
}

function getData() {
    console.log("Boton presionado");
    msj_datos.style.display = "none";
    table.style.display = "none";
    msj_error.style.display = "none";
    msj_sran.style.display = "none";

    msj_datos.innerHTML = '';
    table.innerHTML = '';
    msj_error.innerHTML = '';
    msj_sran.innerHTML = '';

    cellid = input.value;

    if(cellid.length >= 5){
 
        if(NumText(cellid) == true){

            /* modifica el tipo de boton */
            boton.classList.remove('btn-success');
            boton.classList.add('btn-secondary');
            /* muestra el simbolo de carga */
            loader.style.display = "block";
            /* anula el efecto del puntero en el boton */
            boton.style.pointerEvents = "none";
            /* anula el efecto de apretar del enter dentro del input cuando está el simbolo de carga */
            input.addEventListener("keydown", function(event){
                if(event.code == "Enter"){
                    if(loader.style.display == "block"){
                        event.preventDefault()
                    }
                }
            });
        
            axios.get(`http://localhost:5000/api/${cellid}&${checkbox.value}`)
            .then(function (response) {
                console.log(cellid);
            	console.log(response.data); //Me muestra la parte de datos del paquete HTTP que devuelve el GET

                let flag_Telnet = response.data[cellid].flag_Telnet;

                if(flag_Telnet == true){

                    let flag_cellid = response.data[cellid].flag_cellid;
                    let flag_BSC = response.data[cellid].flag_BSC;

                    if(flag_cellid == true && flag_BSC == true){

                        let matriz_BCF = response.data[cellid].matriz_BCF;
                        let flag_SRAN = response.data[cellid].flag_SRAN;
                        let matriz_ET = response.data[cellid].matriz_ET;
                        let alarmas_ET = response.data[cellid].alarmas_ET;
                        let BSC = response.data[cellid].BSC;
                        let ip = response.data[cellid].ip;
                        let BCFs_concat = response.data[cellid].BCF;
                        let flag_BCF = response.data[cellid].flag_BCF;

                        msj_datos.innerHTML = `<div class="alert alert-info max-ancho">
                                                    <strong>Cell-ID: ${cellid}  //  BSC: ${BSC}  //  IP: ${ip}  //  BCF: ${BCFs_concat}</strong>
                                               </div>`;

                        table.innerHTML = render_tabla(flag_SRAN, matriz_BCF, matriz_ET, alarmas_ET);
                                
                        if (flag_SRAN == true){
                            msj_sran.innerHTML = `<div class="alert alert-warning max-ancho">
                                                    <strong>2G SRAN</strong>
                                                  </div>`;
                        }

                        if(checkbox.value == 'on'){

                            intervalRequest = setInterval(update_values,3000);

                            input.style.display = "none";
                            boton.style.display = "none";
                            linea_default.style.display = "none";
                            container_checkbox.style.display = "none";

                            let TresMinutos = 60 * 3;

                            startTimer(TresMinutos, intervalRequest);
                            container_timer.style.display = "block";

                        }
                    }
                    else if(flag_cellid == false){

                        msj_error.innerHTML = `<div class="alert alert-warning max-ancho">
                                                  <strong>Error: Valor de Cell-ID no encontrado</strong>
                                               </div>`;
                    }
                    else if(flag_BSC == false){

                        let BSC = response.data[cellid].BSC;

                        msj_error.innerHTML = `<div class="alert alert-warning max-ancho">
                                                  <strong>Error: La BSC => ${BSC} no se encuentra cargada</strong>
                                               </div>`;
                    }       
                }
                else{

                    msj_error.innerHTML = `<div class="alert alert-warning max-ancho">
                                                <strong>Error: No se puede establecer conexión con la BSC</strong>
                                            </div>`;
                }

                boton.classList.remove('btn-secondary');
                boton.classList.add('btn-success');
                loader.style.display = "none";
                boton.style.pointerEvents = "auto";

            })
            .catch(function (error) {

                console.log('Error');
                
                msj_error.innerHTML = `<div class="alert alert-warning max-ancho">
                                            <strong>Error: No se pudo realizar la consulta hacia el servidor</strong>
                                        </div>`;
                
                boton.classList.remove('btn-secondary');
                boton.classList.add('btn-success');
                loader.style.display = "none";
                boton.style.pointerEvents = "auto";

            });

            /* Borra el valor ingresado en el input HTML */
            input.value = '';
            /* Muestra los componentes HTML */
            msj_datos.style.display = "block";                     
            table.style.display = "block";
            msj_error.style.display = "block";
            msj_sran.style.display = "block";
        }
        else{

            msj_error.innerHTML = `<div class="alert alert-warning max-ancho">
                                        <strong>Error: Se deben ingresar caracteres alfanumericos</strong>
                                   </div>`;

            msj_error.style.display = "block";
        }
        
    }
}