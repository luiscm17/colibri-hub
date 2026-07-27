---
document_type: research
status: active
implementation: not-started
scope: warehouse/dyehouse
authority: evidence
owner: product
last_reviewed: 2026-07-27
---

# SISTEMA SIC JAC - TINTORERIA

El apartado de reportes que es enviado a Jhoselin de tintoreria es muy similar al resto consta de las mismas celdas pero trabajan con diferentes categorias, sub categorias e items

## Esquema del reporte

```
|Codigo|Descripcion|Unidad|Saldo a (Fecha de un dia anterior al inicio del reporte)|Entrada       |Salida        |saldos        |
|      |           |      |Cantidad                      |Valor                    |Cantidad|valor|Cantidad|Valor|Cantidad|Valor|
```

* Codigo: depende de que se maneje si se maneja categorias se usa el numero de la categoria anteriormente asignada en el sistema como: Colorantes o Insumos quimicos. La sub categoria igualmente anteriormente asignado en sistema como: colorantes o quimicos. En el caso del item se coloca su numero de lote o algun diferenciador puesta para cada item
* Descripcion: Describe el producto este dependera de la categoria y la sub categoria, al agregar el item se añade a que categoria pertenece y en que sub categoria se divide
* Unidad: Describe en que unidad se mide si en kilos o litros mayormente en esta tabla se usan kilos
* Saldo a (Un dia anterior a la fecha inicio del reporte): Es el stock que se tenia antes de iniciar el reporte este se añade a las entradas y se resta con las salidas para tener la informacion de los productos que aun no se vendieron durante el reporte, tiene dos secciones una que indica cuantos productos tiene en existencia (cantidad) y la otra que indica cuanto es el valor monetario de dicha cantidad (valor)
* Entradas: Son todos los productos añadidos durante el reporte que tambien se divide en dos secciones la de la cantidad de porductos añadidos a la fecha (cantidad) y el apartado de el valor de los productos añadidos a la fecha que siempre se expresa en Bolivianos (valor)
* Salidas: Son todos los productos vendidos durante el reporte incluyendo a el stock un dia anterior al reporte y las entradas estas juntas se restan con las salidas y dan una nueva cantidad al stock al final del reporte este tambien se divide en dos secciones la cantidad de productos vendidos (Cantidad) y el valor general de los productos vendidos (Valor)
* Saldos: Es el Stock final que se tiene del reporte este apartado es generado automaticamente con la siguiente formula:
(Saldos a partir de (Fecha de un dia anterior al reporte) + Entradas (Durante el reporte)) - Salidas (Durante el reporte) = Saldos.
Igual esta divido en dos secciones una que indica la cantidad de producto en stock (cantidad) y la otra el valor general de lote (valor)

## Entradas

El apartado de ingresos esta seccionado por los detalles para el ingreso de nuevo material al apartado de de las entradas la informacion requerida del SIC JAC es la siguiente:

* N. Ingreso: Este es rellenado automaticamente por el sistema su funcion es ser un contador
* Nota de recepcion: Este apartado se deja en blanco no es necesario para el sistema de administracion q se lleva acabo en la empresa
* Fecha
* Tipo de cambio: Es la conversion de dolares a bolivianos q se utiliza
* Fuente (Recursos): De donde esta saliendo el producto como ser 'Recursos propios' (se queda fijo en el sistema)
* Tipo de ingreso: Es que como esta ingresando al almacen pueden ser: 'Ingreso a almacen', 'Prestamo', 'Muestra' O 'Inventario'
* Proovedor: Se refiere a quien esta dando el producto como ser: 'Almacen illampu', 'Quimifar' y demas proveedores
* Concepto: Un resumen q indica como llego el producto
* Autorizado por: Se refiere a quien da el permiso para que el producto sea ingresado
* Entregado a: se refiere a que encargado esta siendo entregado el producto

## Salidas

El apartado de salidas ingresa la informacion que se requiere para saber que un producto fue vendido o ya esta fuera del almacen en este igual se toman en cuenta varios detalles:

* N. Salida: Este es ingresado automaticamente por el sistema como un contador
* Nota de Entrega: Este se refiere al conteo de facturas que lleva internamente la empresa
* Fecha
* Tipo de Cambio: Este se refiere a la conversion de dolares a bolivianos manejados en la actualidad
* Tipo de Salida: Es el como esta saliendo de almacen como ser 'Salida de almacen', 'Prestamo' o 'Devolucion'
* Destino (Cliente): Es a quien fue vendido o entregado el producto
* Autorizado por: Es quien esta a cargo de la entrega o venta
* Concepto: Un pequeño resumen de por que esta saliendo o como esta saliendo
* Entregado a: Un encargado del almacen

## Ingresos

Es el apartado para añadir items a la base de datos proporciendo la informacion requerida para ser almacenada como ser:

* Codigo: Este es puesto manualmente por la empresa haciendo referencia a su codigo propio de un item
* Categoria: Es a donde pertenece el item como ser 'Colorantes' o 'Insumos quimicos'
* Sub Categoria: Es la parte mas especifica de a donde pertenece como ser 'Colorantes', 'Colorantes ant' o 'Quimicos'
* Descripcion: Es el como se llama el item mas una breve descripcion de este
* Unidad: Es la unidad de medida que maneja el item como ser 'Kilos'

## Tipos de Categorias

* Colorantes
* Insumos Quimicos

## Tipos de Sub Categorias

* Colorantes
* Quimicos

## Items manejados

* Colorantes y su respectivo color y porcentaje
* Quimicos con su respectivo codigo
