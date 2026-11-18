/* Steins;OS installer slideshow: original text slides, no external assets except slide1.png (generated at build). */
import QtQuick 2.0;
import calamares.slideshow 1.0;

Presentation {
    id: presentation

    // Slide.qml reserves margins around each slide. Paint those too, so
    // QQuickWidget's default white clear colour never forms a bright frame.
    Rectangle { anchors.fill: parent; color: "#1b232a"; z: -1 }

    function nextSlide() { presentation.goToNextSlide(); }

    Timer {
        id: advanceTimer
        interval: 15000
        running: presentation.activatedInCalamares
        repeat: true
        onTriggered: nextSlide()
    }

    Slide {
        Rectangle { anchors.fill: parent; color: "#1b232a" }
        Image { id: art; source: "slide1.png"; anchors.top: parent.top; anchors.horizontalCenter: parent.horizontalCenter
                width: parent.width * 0.62; height: width * 0.5625; fillMode: Image.PreserveAspectFit; smooth: true }
        Text { anchors.top: art.bottom; anchors.topMargin: 18; anchors.horizontalCenter: parent.horizontalCenter
               width: parent.width * 0.8; horizontalAlignment: Text.AlignHCenter; wrapMode: Text.WordWrap
               color: "#e7e2d6"; font.pixelSize: 20
               text: "Installing Steins;OS. A Debian 13 and XFCE desktop in graphite and amber." }
    }
    Slide {
        Rectangle { anchors.fill: parent; color: "#1b232a" }
        Column { anchors.centerIn: parent; width: parent.width * 0.8; spacing: 14
            Text { width: parent.width; color: "#e99a45"; font.pixelSize: 28; font.bold: true; wrapMode: Text.WordWrap; text: "Six worldlines" }
            Text { width: parent.width; color: "#e7e2d6"; font.pixelSize: 18; wrapMode: Text.WordWrap
                   text: "One number from 0 to 6 chooses the colours and wallpaper. Open a terminal and run ibm5100 after you log in." } }
    }
    Slide {
        Rectangle { anchors.fill: parent; color: "#1b232a" }
        Column { anchors.centerIn: parent; width: parent.width * 0.8; spacing: 14
            Text { width: parent.width; color: "#e99a45"; font.pixelSize: 28; font.bold: true; wrapMode: Text.WordWrap; text: "Real readings, fictional number" }
            Text { width: parent.width; color: "#e7e2d6"; font.pixelSize: 18; wrapMode: Text.WordWrap
                   text: "The divergence number and D-Mail are decorative and stay on your computer. CPU, memory, disk and uptime readings are real." } }
    }
    Slide {
        Rectangle { anchors.fill: parent; color: "#1b232a" }
        Column { anchors.centerIn: parent; width: parent.width * 0.8; spacing: 14
            Text { width: parent.width; color: "#e99a45"; font.pixelSize: 28; font.bold: true; wrapMode: Text.WordWrap; text: "A development preview" }
            Text { width: parent.width; color: "#e7e2d6"; font.pixelSize: 18; wrapMode: Text.WordWrap
                   text: "Debian provides updates and security fixes for installed packages. Steins;OS is an unofficial fan-inspired project and is not certified for production use. The User guide in the application menu works offline." } }
    }

    function onActivate() { }
    function onLeave() { }
}
